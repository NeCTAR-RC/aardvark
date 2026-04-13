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

from functools import wraps

import aardvark.conf
from aardvark import exception
from aardvark.notifications import base
from aardvark.notifications import events
from aardvark.objects import resources as resources_obj
from aardvark.reaper import job_manager
from aardvark.reaper import reaper_action as ra
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


CONF = aardvark.conf.CONF


def check_old_notification(fn):
    @wraps(fn)
    def decorator(self, ctxt, publisher_id, event_type, payload, metadata):
        if CONF.notification.old_notification != -1 and metadata is not None:
            since = utils.seconds_since(
                metadata["timestamp"], regex="%Y-%m-%d %H:%M:%S.%f"
            )
            if CONF.notification.old_notification < since:
                # Older notifications are discarded
                uuids = self.instances_from_payload(payload)
                LOG.info(
                    "Discarding old event: %s from: %s with uuid: %s for "
                    "instance(s): %s. (since = %s)",
                    event_type,
                    metadata["timestamp"],
                    metadata["message_id"],
                    ", ".join(uuids),
                    since,
                )
                self._pre_discard_hook(payload)
                return self.handled()
        return fn(self, ctxt, publisher_id, event_type, payload, metadata)

    return decorator


class SchedulingEndpoint(base.NotificationEndpoint):
    event_types = ["scheduler.select_destinations.error"]

    def __init__(self):
        super().__init__()

    @check_old_notification
    def error(self, ctxt, publisher_id, event_type, payload, metadata):
        # Store the info in the database
        LOG.info("Received new scheduling info")
        event = events.SchedulingEvent.from_payload(payload)
        try:
            event.create()
        except exception.DBException:
            LOG.error(
                "An exception occurred while storing scheduling info for request_id: %s",
                event.request_id,
            )
            pass
        return self._default_action()

    def instances_from_payload(self, payload):
        event = events.SchedulingEvent.from_payload(payload)
        return event.instance_uuids


class StateUpdateEndpoint(base.NotificationEndpoint):
    event_types = ["instance.update"]

    def __init__(self):
        super().__init__()
        self.job_manager = job_manager.JobManager()

    @check_old_notification
    def info(self, ctxt, publisher_id, event_type, payload, metadata):
        event = events.StateUpdateEvent.from_payload(payload)
        if event.is_failed_build() or event.is_failed_rebuild():
            if event.is_failed_build():
                event_type = ra.ActionEvent.BUILD_REQUEST
            else:
                event_type = ra.ActionEvent.REBUILD_REQUEST

            # Persist the event here, since it's of interest.
            event.create()
            event.set_handled()
            try:
                self.trigger_reaper(
                    event.instance_uuid,
                    event.flavor,
                    event.image,
                    event_type,
                    event.is_bfv,
                )
            except exception.RetriesExceeded:
                LOG.error(
                    "Couldn't find the scheduling info for instance %s. Returning.",
                    event.instance_uuid,
                )
                # The notification is going to be set as handled in order to
                # avoid handling it over and over again.
                self._reset_instances([event.instance_uuid])
                return self.handled()
            except Exception as e:
                LOG.error(
                    "Exception raised while handling request for %s: %s",
                    event.instance_uuid,
                    e,
                )
                self._reset_instances([event.instance_uuid])
                return self.handled()
        return self._default_action()

    @utils.retries(exception.RetriesExceeded)
    def trigger_reaper(self, uuid, flavor, image, event_type, is_bfv=False):
        try:
            # No default value in order to retry
            info = events.SchedulingEvent.get_by_instance_uuid(uuid)
            info.set_handled(instance_uuid=uuid, handled=True)
        except exception.DBException:
            # Maybe there is a race. Raising RetryException to rerty
            LOG.debug("Retrying to retrieve info for uuid <%s>", uuid)
            raise exception.RetryException()

        if info.retries >= CONF.notification.max_handling_retries:
            LOG.info(
                "Retries for instance %s exceeded. Setting event to "
                "handled and returning",
                uuid,
            )
            self._reset_instances([uuid])
            return

        LOG.info(
            "Notification received for uuid: %s event type: %s",
            uuid,
            event_type,
        )
        # Enrich the request with info from the scheduling_info
        request = resources_obj.Resources.obj_from_payload(
            flavor, is_bfv=is_bfv
        )
        LOG.info("Requesting for these resources: %s", request)
        uuids = info.instance_uuids

        if info.multiple_instances and event_type != "rebuild":
            unhandled_events = info.count_scheduling_instances(handled=False)
            if unhandled_events != 0:
                # Wait until the last instance for this request is set to the
                # Pending state, bundle the requests and trigger the reaper
                # once for all of them.
                LOG.info("Bundling up requests for multiple instances.")
                return

        reaper_request = rr_obj.ReaperRequest(
            uuids, info.project_id, request, image, event_type, info.aggregates
        )
        try:
            self.job_manager.post_job(reaper_request)
        except exception.ReaperException as e:
            LOG.error(e.message)
            self._reset_instances(uuids)

    def instances_from_payload(self, payload):
        event = events.StateUpdateEvent.from_payload(payload)
        return [event.instance_uuid]

    def _pre_discard_hook(self, payload):
        event = events.StateUpdateEvent.from_payload(payload)
        if event.is_failed_build() or event.is_failed_rebuild():
            # If instance went into pending and we have to
            # discard the notification, just reset it to ERROR
            self._reset_instances([event.instance_uuid])
