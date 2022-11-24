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


from oslo_context import context
from oslo_log import log
from oslo_service import periodic_task
from oslo_service import service
from taskflow.utils import threading_utils

import aardvark.conf
from aardvark.notifications import manager
from aardvark.reaper import job_manager
from aardvark.reaper import reaper
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


class ReaperService(service.Service):

    def __init__(self):
        super(ReaperService, self).__init__()
        from taskflow.utils import eventlet_utils as _eu  # noqa
        try:
            import eventlet as _eventlet  # noqa
        except ImportError:
            pass
        self.reaper_instances = []
        self._setup_workers(utils.map_aggregate_names())
        self._setup_notification_manager()

    def start(self):
        super(ReaperService, self).start()
        self._start_workers()
        self._start_state_calculation()
        self._start_notification_handling()
        self._start_periodic_killer()

    def stop(self, graceful=True):
        self._stop_workers()
        self._stop_notification_handling()
        # No need to need to explicitly stop the periodic tasks,
        # since it is taken care of by the Service.stop()
        super(ReaperService, self).stop(graceful=graceful)

    @utils.enabled(CONF.reaper.is_multithreaded)
    def _start_workers(self):
        LOG.info('Starting Reaper workers')
        for instance in self.reaper_instances:
            instance.worker.start()

        # Start a periodic task checking the health of the reaper workers
        self.worker_inspector = ReaperWorkerHealthCheck(self.reaper_instances)
        LOG.info('Starting Periodic Worker HealthCheck')
        self.tg.add_dynamic_timer(
            self.worker_inspector.periodic_tasks,
            context=context.get_admin_context())

    @utils.enabled(CONF.aardvark.enable_watermark_mode)
    def _start_state_calculation(self):
        self.state_calculator = SystemStateCalculator()
        LOG.info('Starting Periodic System State Calculation')
        admin_context = context.get_admin_context()
        self.tg.add_dynamic_timer(
            self.state_calculator.periodic_tasks,
            periodic_interval_max=CONF.aardvark.periodic_interval,
            context=admin_context)

    @utils.enabled(CONF.aardvark.enable_periodic_killer)
    def _start_periodic_killer(self):
        self.old_instance_killer = OldPreemptibleKiller()
        LOG.info('Starting Periodic Killer')
        admin_context = context.get_admin_context()
        self.tg.add_dynamic_timer(
            self.old_instance_killer.periodic_tasks,
            periodic_interval_max=CONF.aardvark.killer_interval,
            context=admin_context)

    @utils.enabled(CONF.aardvark.enable_notification_handling)
    def _start_notification_handling(self):
        LOG.info('Starting Notification listener')
        self.notification_manager.start()

    @utils.enabled(CONF.reaper.is_multithreaded)
    def _stop_workers(self):
        LOG.info('Stoping Reaper workers')
        for instance in self.reaper_instances:
            instance.stop_handling()
            instance.worker.join()

    @utils.enabled(CONF.aardvark.enable_notification_handling)
    def _stop_notification_handling(self):
        LOG.info('Stoping Notification listener')
        self.notification_manager.stop()

    @utils.enabled(CONF.reaper.is_multithreaded)
    def _setup_workers(self, watched_aggregates):
        if len(watched_aggregates) == 0:
            LOG.debug('One worker for all infrastructure will be started')
            watched_aggregates = [watched_aggregates]

        for aggregates in watched_aggregates:
            if not isinstance(aggregates, list):
                aggregates = [aggregates]
            instance = reaper.Reaper(aggregates)
            instance.worker = threading_utils.daemon_thread(
                instance.job_handler)
            self.reaper_instances.append(instance)

    @utils.enabled(CONF.aardvark.enable_notification_handling)
    def _setup_notification_manager(self):
        self.notification_manager = manager.ListenerManager()


class SystemStateCalculator(periodic_task.PeriodicTasks):

    def __init__(self):
        super(SystemStateCalculator, self).__init__(CONF)
        self.watched_aggregates = utils.map_aggregate_names()
        if self.watched_aggregates == []:
            self.watched_aggregates = [self.watched_aggregates]
        self.job_manager = job_manager.JobManager()

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=CONF.aardvark.periodic_interval,
                                 run_immediately=True)
    def calculate_system_state(self, context, startup=True):
        LOG.debug('Periodic Timer for state check expired ')
        for aggregates in self.watched_aggregates:
            request = rr_obj.StateCalculationRequest(aggregates)
            self.job_manager.post_job(request)


class ReaperWorkerHealthCheck(periodic_task.PeriodicTasks):

    def __init__(self, reaper_instances):
        super(ReaperWorkerHealthCheck, self).__init__(CONF)
        self.reaper_instances = reaper_instances

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=20, run_immediately=False)
    def check_worker_state(self, context, startup=True):
        LOG.debug('Periodic Timer for worker health check expired')
        dead = []
        for instance in self.reaper_instances:
            if not instance.worker.is_alive() or instance.missed_acks > 5:
                LOG.error('Worker for aggregates %s, found dead.',
                         instance.aggregates)
                instance.stop_handling()
                instance.worker.join(timeout=0.1)
                dead.append(instance)
            else:
                # Each worker will reset this to 0. If the worker is stuck
                # after 3 periodic checks then it is presumed dead and it's
                # revived.
                instance.missed_acks += 1

        for instance in dead:
            self.reaper_instances.remove(instance)
            LOG.info('Reviving worker for aggregates %s.',
                     instance.aggregates)
            new_instance = reaper.Reaper(instance.aggregates)
            new_instance.worker = threading_utils.daemon_thread(
                new_instance.job_handler)
            self.reaper_instances.append(new_instance)
            new_instance.worker.start()


class OldPreemptibleKiller(periodic_task.PeriodicTasks):

    def __init__(self):
        super(OldPreemptibleKiller, self).__init__(CONF)
        self.job_manager = job_manager.JobManager()

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=CONF.aardvark.killer_interval,
                                 run_immediately=False)
    def kill_old_instances(self, context, startup=True):
        LOG.debug('Checking for old instances')
        request = rr_obj.OldInstanceKillerRequest()
        self.job_manager.post_job(request)
