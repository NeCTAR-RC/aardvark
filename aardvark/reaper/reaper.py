# Copyright (c) 2018 European Organization for Nuclear Research.
# All Rights Reserved.
#
#    Licensed under the Apache License, Version 2.0 (the "License"); you may
#    not use this file except in compliance with the License. You may obtain
#    a copy of the License at
#
#         http://www.apache.org/licenses/LICENSE-2.0
#
#    Unless required by applicable law or agreed to in writing, software
#    distributed under the License is distributed on an "AS IS" BASIS, WITHOUT
#    WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied. See the
#    License for the specific language governing permissions and limitations
#    under the License.


import functools
from novaclient import exceptions as n_exc
from stevedore import driver
import time
import traceback

from aardvark.api import nova
from aardvark.api import placement
import aardvark.conf
from aardvark import exception
from aardvark.objects import instance as instance_obj
from aardvark.objects import resources as resources_obj
from aardvark.objects import system as system_obj
from aardvark.reaper import reaper_action as ra
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils

from oslo_log import log as logging

from taskflow import exceptions as excp
from taskflow.jobs import backends


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


def while_running(fn):
    @functools.wraps(fn)
    def wrapper(self, board):
        while self.flag:
            fn(self, board)
    return wrapper


def reaper_action(fn):
    @functools.wraps(fn)
    def wrapper(self, request):
        action = ra.ReaperAction()
        if isinstance(request, rr_obj.ReaperRequest):
            action.requested_instances = request.uuids
        action.event = request.event_type
        action.state = ra.ActionState.ONGOING
        action.create()
        self.notify_about_action(action)
        try:
            victims = fn(self, request)
            action.victims = victims
            action.state = ra.ActionState.SUCCESS
        except exception.PreemptibleRequest:
            action.state = ra.ActionState.CANCELED
            action.fault_reason = traceback.format_exc()
        except exception.AardvarkException:
            action.state = ra.ActionState.FAILED
            action.fault_reason = "Request:\n%s\n\n%s" % (
                    request.to_dict(), traceback.format_exc())
        except Exception:
            action.state = ra.ActionState.FAILED
            action.fault_reason = "Request:\n%s\n\n%s" % (
                    request.to_dict(), traceback.format_exc())
        finally:
            action.update()
        self.notify_about_action(action)
    return wrapper


class Reaper(object):
    """The Reaper Class

    This class decides which preemptible servers have to be terminated.
    """
    def __init__(self, aggregates=None):
        self.worker = None
        self.missed_acks = 0

        self.aggregates = aggregates if aggregates else []
        # TODO(ttsiouts): Load configured notification system in order to
        # notify the owner of the server that will be terminated
        self.notifiers = self._load_enabled_notifiers()

    def _load_configured_strategy(self, watermark_mode=False):
        """Loads the configured strategy"""
        return driver.DriverManager(
            "aardvark.reaper.strategy",
            CONF.reaper.strategy,
            invoke_on_load=True,
            invoke_args=tuple([watermark_mode])).driver

    def _load_enabled_notifiers(self):
        """Loads the enabled notifiers"""
        notifiers = list()
        for notifier in CONF.reaper_notifier.enabled_notifiers:
            notification_driver = driver.DriverManager(
                "aardvark.reaper.notifier", notifier,
                invoke_on_load=True).driver
            LOG.info("Loaded %s notifier successfully", notifier)
            notifiers.append(notification_driver)
        return notifiers

    def handle_reaper_request(self, request):
        try:
            self._check_requested_aggregates(request)
            victims = self._do_handle_reaper_request(request)
            self._rebuild_instances(request.uuids, request.image)
            return victims
        except exception.AardvarkException as e:
            LOG.error(e.message)
            self._reset_instances(request.uuids)
            raise
        except Exception as ex:
            LOG.critical("Unexpected error: %s", ex)
            self._reset_instances(request.uuids)
            raise

    def _do_handle_reaper_request(self, request):
        """Main functionality of the Reaper

        Gathers info and tries to free up the requested resources.

        :param req_spec: the request specification for the spawning server
        :param resources: the requested resources
        """
        # If we receive a request without explicit aggregates
        # set the aggregates of the request to self.aggregates
        # so that we don't invalidate the system state of
        # other worker threads by altering the state of resource
        # providers originally not watched by this thread.
        if request.aggregates == [] and self.aggregates[0] != []:
            request.aggregates = self.aggregates

        LOG.info("Handling request for instance(s): %s, aggregates: %s, "
                 "project: %s, resources: %s", request.uuids,
                 request.aggregates, request.project_id, request.resources)

        system = system_obj.System(request.aggregates)

        slots = len(request.uuids)
        preemptible_projects = [
            project.id_ for project in system.preemptible_projects
        ]
        if request.project_id in preemptible_projects:
            # Make space only if the requesting project is
            # non-preemptible.
            raise exception.PreemptibleRequest()
        return self.free_resources(request.resources, system, slots=slots)

    def handle_state_calculation_request(self, request):

        system = system_obj.System(request.aggregates)
        system_state = system.system_state()

        self._delete_locked_instances(system)
        LOG.info("Current System usage = %s", system_state.usage())
        if system_state.usage() > CONF.aardvark.watermark:
            resource_request = system_state.get_excessive_resources(
                CONF.aardvark.watermark)
            LOG.info("Over limit, attempting to cleanup: %s", resource_request)

            try:
                return self.free_resources(resource_request, system,
                                           watermark_mode=True)
            except exception.RetriesExceeded:
                LOG.error("Retries exceeded while freeing resources to "
                          "maintain system usage below %s%. Aborting.",
                          CONF.aardvark.watermark)

    def handle_old_instance_request(self, request):
        system = system_obj.System()
        instance_list = instance_obj.InstanceList()
        old_servers = list()
        self._delete_locked_instances(system)
        for project in system.preemptible_projects:
            filters = {
                'project_id': project.id_,
                'sort_dir': 'asc',
                'sort_key': 'created_at'
            }
            instances = instance_list.instances(**filters)
            for instance in instances:
                lifespan = utils.seconds_since(instance.created)
                if lifespan >= CONF.aardvark.max_life_span:
                    old_servers.append(instance)
                else:
                    # NOTE(ttsiouts): We are fetching the instances
                    # already sotred from the Nova API so when we find the
                    # first instance that is not old enough just break.
                    break
        for server in old_servers:
            self._delete_instance(server,
                                  side_effect=exception.RetryException)
        return [server.uuid for server in old_servers]

    def _delete_locked_instances(self, system):
        instance_list = instance_obj.InstanceList()
        projects = [p.id_ for p in system.preemptible_projects]
        for project_id in projects:
            filters = {
                'project_id': project_id,
                'locked': True,
            }
            instances = instance_list.instances(**filters)
            for instance in instances:
                LOG.info("Deleting locked instance: %s", instance.uuid)
                self._delete_instance(instance)

    @utils.retries(exception.RetriesExceeded)
    def free_resources(self, request, system, slots=1, watermark_mode=False):

        reaper_strategy = self._load_configured_strategy(
            watermark_mode=watermark_mode)

        hosts = system.resource_providers
        projects = [p.id_ for p in system.preemptible_projects]

        selected_hosts, selected_servers = \
            reaper_strategy.get_preemptible_servers(request, hosts,
                                                    slots, projects)

        for server in selected_servers:
            self._delete_instance(server,
                                  side_effect=exception.RetryException)

        # We have to wait until the allocations are removed
        if len(selected_servers) > 0:
            self.wait_until_allocations_are_deleted(selected_servers[:])

        return [server.uuid for server in selected_servers]

    def notify_about_instance(self, instance):
        for notifier in self.notifiers:
            try:
                notifier.notify_about_instance(instance)
            except Exception as e:
                LOG.error("Error while notifying for instance %s: %s",
                          instance.uuid, e)
                continue

    def notify_about_action(self, action):
        for notifier in self.notifiers:
            try:
                notifier.notify_about_action(action)
            except Exception as e:
                LOG.error("Error while notifying for action %s: %s",
                          action.uuid, e)
                continue

    def job_handler(self):
        self.flag = True

        backend_conf = {
            'board': CONF.reaper.job_backend,
            'path': "/var/lib/%s" % CONF.reaper.job_backend,
            'host': CONF.reaper.backend_host
        }

        with backends.backend("ReaperBoard", backend_conf.copy()) as board:
            self.attempt_job_claim(board)

        LOG.info("Reaper worker stopped: %s", self.aggregates)

    @while_running
    def attempt_job_claim(self, board):

        # Reset the acks in every loop to show you're alive
        self.missed_acks = 0
        jobs = board.iterjobs(ensure_fresh=True, only_unclaimed=True)
        for job in jobs:
            try:
                request = rr_obj.request_from_job(job.details)
                self._check_requested_aggregates(request)
                board.claim(job, "worker")
                LOG.debug("Claimed %s", job)
            except exception.UnknownRequestType:
                continue
            except exception.UnwatchedAggregate:
                continue
            except (excp.UnclaimableJob, excp.NotFound):
                # Another worker maybe claimed the job. No need to
                # take further actions.
                continue

            self.handle_request(request)
            board.consume(job, "worker")
            LOG.debug("Consumed %s", job)

    @reaper_action
    def handle_request(self, request):

        if isinstance(request, rr_obj.ReaperRequest):
            return self.handle_reaper_request(request)

        elif isinstance(request, rr_obj.StateCalculationRequest):
            return self.handle_state_calculation_request(request)

        elif isinstance(request, rr_obj.OldInstanceKillerRequest):
            return self.handle_old_instance_request(request)

    def stop_handling(self):
        self.flag = False

    def _rebuild_instances(self, uuids, image):
        for uuid in uuids:
            try:
                LOG.info("Trying to rebuild server with uuid: %s", uuid)
                nova.server_rebuild(uuid, image)
            except n_exc.NotFound:
                # Looks like we were late, and the server is deleted.
                # Nothing more we can do.
                LOG.info("Server with uuid: %s, not found.", uuid)
                continue
            LOG.info("Request to rebuild the server %s was sent.", uuid)

    def _reset_instances(self, uuids):
        for uuid in uuids:
            try:
                LOG.info('Trying to reset server %s to error', uuid)
                nova.server_reset_state(uuid)
            except n_exc.NotFound:
                # Looks like we were late, and the server is deleted.
                # Nothing more we can do.
                LOG.info("Server with uuid: %s, not found.", uuid)
                continue
            LOG.info("Request to reset the server %s was sent.", uuid)

    def _check_requested_aggregates(self, request):
        if self.aggregates == []:
            return
        watched = set(self.aggregates)
        requested = set(request.aggregates)
        common = list(watched & requested)
        if len(common) == 0 and len(request.aggregates) != 0:
            LOG.error('Request for not watched aggregates %s',
                      request.aggregates)
            raise exception.UnwatchedAggregate()
        request.aggregates = list(common)
        return

    @utils.timeit
    def wait_until_allocations_are_deleted(self, servers, timeout=20):
        """Wait until the allocation is deleted

        Tries to get the allocations of a given instance until it's not found
        or the timeout exceeds
        """
        # Awful way to wait until the allocation is removed.....
        # Have to live with it for now... If we don't wait here, the claiming
        # of the resources will most probably fail since placement will not be
        # updated right away....
        target = resources_obj.Resources()
        start = time.time()
        now = start
        while now - start <= timeout:
            not_found = False
            for server in servers:
                resources = placement.get_consumer_allocations(server.uuid,
                                                               server.rp_uuid)
                if resources == target:
                    not_found = True
                    break
            if not_found:
                LOG.info('Allocations for %s not found', server.uuid)
                servers.remove(server)
            if len(servers) == 0:
                break
            now = time.time()

    def _delete_instance(self, server, side_effect=None):
        try:
            LOG.info("Trying to delete server: %s", server.name)
            if nova.server_delete(server.uuid):
                self.notify_about_instance(server)
        except n_exc.NotFound:
            LOG.info("Server %s not found.", server.name)
            if side_effect:
                raise side_effect()
