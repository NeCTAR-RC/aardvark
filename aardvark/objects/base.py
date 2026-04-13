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


class BaseObject:
    def __init__(self, *args, **kwargs):
        pass


class PlacementObject(BaseObject):
    def __init__(self, *args, **kwargs):
        pass


class PersistentObject:
    """Base class for all objects stored in aardvark DB"""

    fields = []
    enum_fields = {}
    db_map = {}

    def __init__(self):
        object.__setattr__(self, "changes", {})

    def __setattr__(self, attr, value):
        self.changes[attr] = value
        if attr in self.enum_fields:
            self.changes[attr] = value.value
        super().__setattr__(attr, value)

    def reset_changes(self):
        self.changes = {}

    @classmethod
    def from_db_object(cls, db_object):
        obj = cls()
        for field in cls.fields:
            try:
                if field not in cls.db_map:
                    value = getattr(db_object, field)
                else:
                    value = getattr(db_object, cls.db_map[field])
                if field in cls.enum_fields:
                    value = cls.enum_fields[field](value)
            except TypeError:
                value = None
            setattr(obj, field, value)
        return obj

    def obj_get_changes(self):
        return self.changes
