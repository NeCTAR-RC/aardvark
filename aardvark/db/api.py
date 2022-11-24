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

import abc

from oslo_config import cfg
from oslo_db import api as db_api


_BACKEND_MAPPING = {'sqlalchemy': 'aardvark.db.sqlalchemy.api'}
IMPL = db_api.DBAPI.from_config(cfg.CONF, backend_mapping=_BACKEND_MAPPING,
                                lazy=True)


def get_instance():
    """Return a DB API instance."""
    return IMPL


class Connection(object, metaclass=abc.ABCMeta):
    """Base class for storage connections."""

    @abc.abstractmethod
    def __init__(self):
        """Contructor."""

    @abc.abstractmethod
    def create_scheduling_event(self, values):
        """Create a scheduling event"""

    @abc.abstractmethod
    def create_instance_scheduling_event(self, values):
        """Create a scheduling event for an instance"""

    @abc.abstractmethod
    def update_scheduling_event(self, event_uuid, values):
        """Update a scheduling event"""

    @abc.abstractmethod
    def get_instance_scheduling_event(self, instance_uuid, handled=False):
        """Get an instance scheduling event"""

    @abc.abstractmethod
    def get_scheduling_event_by_request_id(self, request_id):
        """Get a scheduling event based on the request_id"""

    @abc.abstractmethod
    def list_scheduling_event_instances(self, event_uuid):
        """List the instance scheduling events given the uuid of an event"""

    @abc.abstractmethod
    def update_instance_scheduling_event(self, scheduling_event_uuid, values,
                                         instance_uuid=None):
        """Update an instance scheduling event"""

    @abc.abstractmethod
    def count_instance_scheduling_events(self, scheduling_event_uuid, handled):
        """Counts the instances related to a scheduling event"""

    @abc.abstractmethod
    def create_state_update_event(self, values):
        """Create a state_update_event"""

    @abc.abstractmethod
    def get_state_update_event_by_instance(self, instance_uuid, handled=False):
        """Get a state_update_event based on the instance_uuid"""

    @abc.abstractmethod
    def get_state_update_event_by_uuid(self, uuid):
        """Get a state_update_event based on the uuid"""

    @abc.abstractmethod
    def update_instance_state_update_event(self, event_uuid, instance_uuid,
                                           values):
        """Update a state update event"""

    @abc.abstractmethod
    def create_reaper_action(self, values):
        """Create a reaper action"""

    @abc.abstractmethod
    def get_reaper_action_by_uuid(self, uuid):
        """Get a reaper action by uuid"""

    @abc.abstractmethod
    def list_reaper_actions(self):
        """List reaper actions"""

    @abc.abstractmethod
    def get_reaper_action_by_instance(self, uuid):
        """Get a reaper action by requested instance uuid"""

    @abc.abstractmethod
    def get_reaper_action_by_victim(self, uuid):
        """Get a reaper action by victim instance uuid"""

    @abc.abstractmethod
    def update_reaper_action(self, uuid, values):
        """Update a reaper action"""
