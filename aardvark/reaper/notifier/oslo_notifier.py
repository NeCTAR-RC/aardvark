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

import enum
from functools import wraps

import aardvark.conf
from aardvark.reaper.notifier import base
from aardvark.reaper import reaper_action as ra

from oslo_context import context
from oslo_log import log as logging
import oslo_messaging as messaging


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


class AardvarkNotification:
    fields = []
    event_type = None

    def get_payload_from_object(self, obj):
        payload = dict()
        for field in self.fields:
            value = getattr(obj, field, None)
            if isinstance(value, enum.Enum):
                value = value.value.lower()
            payload[field] = value
        return payload


class InstanceTerminationNotification(AardvarkNotification):
    fields = ["user_id", "uuid", "name"]
    event_type = "instance_terminated"


class ReaperActionNotification(AardvarkNotification):
    fields = [
        "state",
        "requested_instances",
        "victims",
        "fault_reason",
        "event",
        "uuid",
    ]
    event_type = "reaper_action"

    def get_payload_from_object(self, action):
        payload = super().get_payload_from_object(action)
        if action.state not in (
            ra.ActionState.FAILED,
            ra.ActionState.CANCELED,
        ):
            del payload["fault_reason"]
        if action.state != ra.ActionState.SUCCESS:
            del payload["victims"]
        if action.event == ra.ActionEvent.STATE_CALCULATION:
            del payload["requested_instances"]
        self.event_type = f"{self.event_type}.{action.state.value.lower()}"
        return payload


def catch_messaging_failure(fn):
    @wraps(fn)
    def decorator(*args, **kwargs):
        try:
            fn(*args, **kwargs)
        except messaging.exceptions.MessagingException as e:
            LOG.error("Oslo notifier failed because of: %s", e)

    return decorator


class OsloNotifier(base.BaseNotifier):
    """Sends oslo notifications"""

    def __init__(self):
        super().__init__()
        notification_transport = messaging.get_notification_transport(CONF)
        self.oslo_notifier = messaging.Notifier(
            notification_transport,
            "aardvark.reaper",
            topics=CONF.reaper_notifier.oslo_topics,
        )
        self.context = context.RequestContext()

    @catch_messaging_failure
    def notify_about_instance(self, instance):
        notification = InstanceTerminationNotification()
        payload = notification.get_payload_from_object(instance)
        self.oslo_notifier.info(self.context, notification.event_type, payload)

    @catch_messaging_failure
    def notify_about_action(self, action):
        notification = ReaperActionNotification()
        payload = notification.get_payload_from_object(action)
        if action.state in (ra.ActionState.FAILED, ra.ActionState.CANCELED):
            self.oslo_notifier.error(
                self.context, notification.event_type, payload
            )
        else:
            self.oslo_notifier.info(
                self.context, notification.event_type, payload
            )
