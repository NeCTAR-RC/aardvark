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

from aardvark.db import api as dbapi
from aardvark.objects import base


class ActionState(enum.Enum):
    ONGOING = "ONGOING"
    SUCCESS = "SUCCESS"
    FAILED = "FAILED"
    CANCELED = "CANCELED"


class ActionEvent(enum.Enum):
    BUILD_REQUEST = "BUILD_REQUEST"
    REBUILD_REQUEST = "REBUILD_REQUEST"
    STATE_CALCULATION = "STATE_CALCULATION"
    KILLER_REQUEST = "KILLER_REQUEST"


class ReaperAction(base.PersistentObject):
    dbapi = dbapi.get_instance()
    enum_fields = {"state": ActionState, "event": ActionEvent}
    fields = [
        "state",
        "requested_instances",
        "victims",
        "fault_reason",
        "event",
        "uuid",
        "created_at",
        "updated_at",
    ]

    def __init__(self):
        super().__init__()

    def create(self):
        values = self.obj_get_changes()
        ref = self.dbapi.create_reaper_action(values)
        self.uuid = ref.uuid
        self.refresh()

    def update(self):
        values = self.obj_get_changes()
        self.dbapi.update_reaper_action(self.uuid, values)
        self.refresh()

    def refresh(self):
        db_obj = ReaperAction.get_by_uuid(self.uuid)
        new = ReaperAction.from_db_object(db_obj)
        for field in self.fields:
            if hasattr(new, field):
                value = getattr(new, field)
                setattr(self, field, value)
        self.reset_changes()

    @staticmethod
    def get_by_uuid(uuid):
        db_obj = ReaperAction.dbapi.get_reaper_action_by_uuid(uuid)
        return ReaperAction.from_db_object(db_obj)

    @staticmethod
    def get_by_instance_uuid(uuid):
        db_objs = ReaperAction.dbapi.get_reaper_action_by_instance(uuid)
        result = []
        for db_obj in db_objs:
            result.append(ReaperAction.from_db_object(db_obj))
        return result

    @staticmethod
    def get_by_victim_uuid(victim_uuid):
        db_objs = ReaperAction.dbapi.get_reaper_action_by_victim(victim_uuid)
        result = []
        for db_obj in db_objs:
            result.append(ReaperAction.from_db_object(db_obj))
        return result

    @staticmethod
    def list_reaper_actions():
        db_objs = ReaperAction.dbapi.list_reaper_actions()
        result = []
        for db_obj in db_objs:
            result.append(ReaperAction.from_db_object(db_obj))
        return result
