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

from aardvark.reaper.notifier import base
from aardvark.reaper import reaper_action as ra

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class LogNotifier(base.BaseNotifier):
    """Creates a log message when called to notify for an instance"""

    def __init__(self):
        super().__init__()

    def notify_about_instance(self, instance):
        LOG.info("Preemptible instance %s was deleted.", instance.uuid)

    def notify_about_action(self, action):
        if action.event == ra.ActionEvent.STATE_CALCULATION:
            self._notify_about_state_calculation(action)
        elif action.event == ra.ActionEvent.KILLER_REQUEST:
            self._notify_about_killer_request(action)
        else:
            self._notify_about_reaper_request(action)

    def _notify_about_reaper_request(self, action):
        if action.state in (ra.ActionState.FAILED, ra.ActionState.CANCELED):
            LOG.error(
                "Reaper request %s, state: %s, requested instances: %s, "
                "event: %s, fault reason: %s",
                action.uuid,
                action.state.value.lower(),
                action.requested_instances,
                action.event.value.lower(),
                action.fault_reason,
            )
        elif action.state == ra.ActionState.SUCCESS:
            LOG.info(
                "Reaper request %s, state: %s, requested instances: %s, "
                "event: %s, victims: %s",
                action.uuid,
                action.state.value.lower(),
                action.requested_instances,
                action.event.value.lower(),
                action.victims,
            )
        else:
            LOG.info(
                "Reaper request %s, state: %s, requested instances: %s, event: %s",
                action.uuid,
                action.state.value.lower(),
                action.requested_instances,
                action.event.value.lower(),
            )

    def _notify_about_state_calculation(self, action):
        if action.state in (ra.ActionState.FAILED, ra.ActionState.CANCELED):
            LOG.error(
                "State calculation %s, state: %s, fault reason: %s",
                action.uuid,
                action.state.value.lower(),
                action.fault_reason,
            )
        elif action.state == ra.ActionState.SUCCESS:
            LOG.info(
                "State calculation %s, state: %s, victims: %s",
                action.uuid,
                action.state.value.lower(),
                action.victims,
            )
        else:
            LOG.info(
                "State calculation %s, state: %s",
                action.uuid,
                action.state.value.lower(),
            )

    def _notify_about_killer_request(self, action):
        if action.state in (ra.ActionState.FAILED, ra.ActionState.CANCELED):
            LOG.error(
                "Killer request %s, state: %s, fault reason: %s",
                action.uuid,
                action.state.value.lower(),
                action.fault_reason,
            )
        elif action.state == ra.ActionState.SUCCESS:
            LOG.info(
                "Killer request %s, state: %s, victims: %s",
                action.uuid,
                action.state.value.lower(),
                action.victims,
            )
        else:
            LOG.info(
                "Killer request %s, state: %s",
                action.uuid,
                action.state.value.lower(),
            )
