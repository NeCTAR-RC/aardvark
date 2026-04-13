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


from aardvark import exception
from aardvark.objects import resources as resources_obj
from aardvark.reaper import reaper_action


def request_from_job(request):
    if request["req_type"] == "ReaperRequest":
        return ReaperRequest.from_primitive(request)
    elif request["req_type"] == "StateCalculationRequest":
        return StateCalculationRequest.from_primitive(request)
    elif request["req_type"] == "OldInstanceKillerRequest":
        return OldInstanceKillerRequest.from_primitive(request)
    else:
        raise exception.UnknownRequestType()


class ReaperRequest:
    def __init__(
        self, uuids, project_id, resources, image, event_type, aggregates=None
    ):
        self.req_type = self.__class__.__name__
        self.uuids = uuids
        self.image = image
        self.project_id = project_id
        self.resources = resources
        self.event_type = event_type
        self.aggregates = aggregates if aggregates else []

    @staticmethod
    def from_primitive(primitive):
        uuids = primitive["uuids"]
        project_id = primitive["project_id"]
        image = primitive["image"]
        resources = resources_obj.Resources(primitive["resources"])
        aggregates = primitive["aggregates"]
        event_type = primitive["event_type"]
        return ReaperRequest(
            uuids,
            project_id,
            resources,
            image,
            event_type,
            aggregates=aggregates,
        )

    def to_dict(self):
        return {
            "req_type": self.req_type,
            "uuids": self.uuids,
            "project_id": self.project_id,
            "resources": self.resources.to_dict(),
            "image": self.image,
            "event_type": self.event_type,
            "aggregates": self.aggregates,
        }

    def __eq__(self, other):
        return (
            self.aggregates == other.aggregates
            and self.uuids == other.uuids
            and self.image == other.image
            and self.project_id == other.project_id
            and self.resources == other.resources
            and self.event_type == other.event_type
        )


class StateCalculationRequest:
    def __init__(self, aggregates):
        self.req_type = self.__class__.__name__
        self.aggregates = aggregates
        self.event_type = reaper_action.ActionEvent.STATE_CALCULATION

    @staticmethod
    def from_primitive(primitive):
        aggregates = primitive["aggregates"]
        return StateCalculationRequest(aggregates)

    def to_dict(self):
        return {"req_type": self.req_type, "aggregates": self.aggregates}

    def __eq__(self, other):
        return (
            self.aggregates == other.aggregates
            and self.req_type == other.req_type
        )


class OldInstanceKillerRequest:
    def __init__(self):
        self.req_type = self.__class__.__name__
        self.event_type = reaper_action.ActionEvent.KILLER_REQUEST

    @staticmethod
    def from_primitive(primitive):
        return OldInstanceKillerRequest()

    def to_dict(self):
        return {
            "req_type": self.req_type,
        }
