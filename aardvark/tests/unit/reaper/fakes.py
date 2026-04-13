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

from aardvark.reaper import reaper_action
from aardvark.reaper import reaper_request
from aardvark.tests.unit.objects import fakes as object_fakes


def make_reaper_action(**kwargs):
    action = reaper_action.ReaperAction()
    action.uuid = kwargs.get("uuid", "fake-action-uuid")
    action.event = kwargs.get("event", reaper_action.ActionEvent.BUILD_REQUEST)
    action.state = kwargs.get("state", reaper_action.ActionState.ONGOING)
    action.victims = kwargs.get("victims", ["fake-victim1", "fake-victim2"])
    action.requested_instances = kwargs.get(
        "requested_instances", ["requested1", "requested2"]
    )
    action.fault_reason = kwargs.get("fault_reason", None)
    return action


def make_reaper_request(
    uuids=None,
    project=None,
    resources=None,
    image=None,
    event_type=None,
    aggregates=None,
):
    uuids = uuids or ["instance_uuid"]
    project = project or ["project_id"]
    resources = resources or object_fakes.make_resources()
    image = image or "image_uuid"
    event_type = event_type or reaper_action.ActionEvent.BUILD_REQUEST
    return reaper_request.ReaperRequest(
        uuids, project, resources, image, event_type, aggregates=aggregates
    )


def make_calculation_request(aggregates=None):
    aggregates = aggregates or ["aggregate1", "aggregate2"]
    return reaper_request.StateCalculationRequest(aggregates)
