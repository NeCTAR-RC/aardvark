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


def make_scheduling_payload(
    instance_uuids, aggregates=None, req_id=1, project="project_id"
):
    payload = {
        "nova_object.data": {
            "instance_uuids": instance_uuids,
            "request_spec": make_request_spec_payload(
                req_id=req_id, aggregates=aggregates, project=project
            ),
        }
    }
    return payload


def make_state_update_payload(
    instance_uuid,
    state,
    old_state,
    image_uuid,
    flavor_uuid,
    old_task=None,
    new_task=None,
):
    state_update = {
        "nova_object.data": {
            "state": state,
            "old_state": old_state,
            "new_task_state": new_task,
            "old_task_state": old_task,
        }
    }

    payload = {
        "nova_object.data": {
            "uuid": instance_uuid,
            "state_update": state_update,
            "image_uuid": image_uuid,
            "flavor": make_flavor_payload(flavor_uuid),
        }
    }

    return payload


def make_flavor_payload(
    uuid, vcpus=1, ephemeral=0, root_gb=20, swap=0, ram=2000
):
    flavor = {
        "nova_object.data": {
            "uuid": uuid,
            "vcpus": vcpus,
            "ephemeral_gb": ephemeral,
            "root_gb": root_gb,
            "swap": swap,
            "memory_mb": ram,
        }
    }
    return flavor


def make_request_spec_payload(req_id=1, aggregates=None, project="uuid"):
    req_spec = {
        "nova_object.data": {
            "id": req_id,
            "project_id": project,
            "requested_destination": make_destination_payload(aggregates),
        }
    }
    return req_spec


def make_destination_payload(aggregates):
    destination = None
    if aggregates:
        destination = {
            "nova_object.data": {"aggregates": [",".join(aggregates)]}
        }

    return destination
