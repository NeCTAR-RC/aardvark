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

from oslo_log import log

from aardvark.api import cinder
from aardvark.db import api as dbapi
from aardvark import exception
from aardvark.notifications import base
from aardvark import utils


LOG = log.getLogger(__name__)


class SchedulingEvent(base.NotificationEvent):
    """Scheduling Event"""

    dbapi = dbapi.get_instance()
    fields = [
        "instance_uuids",
        "request_spec",
        "request_id",
        "retries",
        "uuid",
    ]

    def __init__(self):
        super().__init__()

    @staticmethod
    def from_payload(payload):
        event = SchedulingEvent()
        event.instance_uuids = payload["nova_object.data"]["instance_uuids"]
        event.request_spec = payload["nova_object.data"]["request_spec"]
        event.request_id = event.request_spec["nova_object.data"]["id"]
        event.retries = 0
        return event

    @staticmethod
    def from_db_object(db_object):
        event = SchedulingEvent()
        event.request_spec = db_object.request_spec
        event.request_id = db_object.request_id
        event.uuid = db_object.uuid
        event.retries = db_object.retries
        instances = SchedulingEvent.dbapi.list_scheduling_event_instances(
            event.uuid
        )
        event.instance_uuids = [
            instance.instance_uuid for instance in instances
        ]
        return event

    @property
    def multiple_instances(self):
        return len(self.instance_uuids) > 1

    @property
    def project_id(self):
        return self.request_spec["nova_object.data"]["project_id"]

    @property
    def aggregates(self):
        try:
            d = self.request_spec["nova_object.data"]["requested_destination"]
            aggs = d["nova_object.data"]["aggregates"]
            return aggs[0].split(",")
        except TypeError:
            # In case destination is not set it will be None, so trying to
            # access its items will raise a TypeError.
            return utils.get_default_aggregates()

    @staticmethod
    def get_by_instance_uuid(instance_uuid):
        db_object = SchedulingEvent.dbapi.get_instance_scheduling_event(
            instance_uuid
        )
        return SchedulingEvent.from_db_object(db_object.scheduling_event)

    @staticmethod
    def get_by_request_id(request_id):
        db_object = SchedulingEvent.dbapi.get_scheduling_event_by_request_id(
            request_id
        )
        return SchedulingEvent.from_db_object(db_object)

    def create(self):
        values = {
            "request_id": self.request_id,
            "request_spec": self.request_spec,
            "retries": 0,
        }
        try:
            db_obj = self.dbapi.create_scheduling_event(values)
            self.uuid = db_obj.uuid
            for instance in self.instance_uuids:
                values = {"instance_uuid": instance, "event_uuid": self.uuid}
                self.dbapi.create_instance_scheduling_event(values)
        except exception.SchedulingEventAlreadyExists:
            self = self.get_by_request_id(self.request_id)
            self.set_handled(handled=False)
            self.increase_retries()
        self.refresh()

    def set_handled(self, instance_uuid=None, handled=True):
        values = {"handled": handled}
        if instance_uuid:
            self.dbapi.update_instance_scheduling_event(
                self.uuid, values, instance_uuid=instance_uuid
            )
        else:
            self.dbapi.update_instance_scheduling_event(self.uuid, values)
        self.refresh()

    def increase_retries(self):
        values = {"retries": self.retries + 1}
        ref = self.dbapi.update_scheduling_event(self.uuid, values)
        self = self.from_db_object(ref)
        self.refresh()

    def count_scheduling_instances(self, handled=False):
        return self.dbapi.count_instance_scheduling_events(self.uuid, handled)

    def refresh(self):
        db_obj = SchedulingEvent.get_by_request_id(self.request_id)
        new = SchedulingEvent.from_db_object(db_obj)
        for field in self.fields:
            if hasattr(new, field):
                value = getattr(new, field)
                setattr(self, field, value)
        self.reset_changes()


class StateUpdateEvent(base.NotificationEvent):
    """State Update Event"""

    dbapi = dbapi.get_instance()
    fields = [
        "instance_uuid",
        "state_update",
        "image",
        "flavor",
        "handled",
        "uuid",
        "block_devices",
    ]

    def __init__(self):
        super().__init__()
        self.handled = False

    @staticmethod
    def from_payload(payload):
        event = StateUpdateEvent()
        event.instance_uuid = payload["nova_object.data"]["uuid"]
        event.state_update = payload["nova_object.data"]["state_update"]
        flavor_data = payload["nova_object.data"]["flavor"]["nova_object.data"]
        event.flavor = flavor_data
        try:
            event.block_devices = payload["nova_object.data"]["block_devices"]
            if event.block_devices is None:
                event.block_devices = []
        except KeyError:
            LOG.warning(
                "Notifications from Nova do not contaion"
                " block device mapping. No way to know if"
                " an instance is booting from volume"
            )
            event.block_devices = []
        if event.is_bfv:
            # If the instance boots from volume we need to
            # fetch the image information from the volume.
            event.image = cinder.get_image_from_volume(event.root_volume)
        else:
            event.image = payload["nova_object.data"]["image_uuid"]
        return event

    @staticmethod
    def from_db_object(db_object):
        event = StateUpdateEvent()
        event.state_update = db_object.state_update
        event.instance_uuid = db_object.instance_uuid
        event.image = db_object.image
        event.flavor = db_object.flavor
        event.handled = db_object.handled
        return event

    @property
    def old_state(self):
        return self.state_update["nova_object.data"]["old_state"]

    @property
    def new_state(self):
        return self.state_update["nova_object.data"]["state"]

    @property
    def old_task_state(self):
        return self.state_update["nova_object.data"]["old_task_state"]

    @property
    def new_task_state(self):
        return self.state_update["nova_object.data"]["new_task_state"]

    def is_failed_build(self):
        return self.old_state == "building" and self.new_state == "pending"

    def is_failed_rebuild(self):
        return (
            self.new_state == "pending"
            and self.old_task_state == "rebuilding"
            and self.new_task_state is None
        )

    @property
    def is_bfv(self):
        return any(
            [
                bdm["nova_object.data"]["boot_index"] == 0
                for bdm in self.block_devices
            ]
        )

    @property
    def root_volume(self):
        root_volumes = [
            bdm["nova_object.data"]["volume_id"]
            for bdm in self.block_devices
            if bdm["nova_object.data"]["boot_index"] == 0
        ]
        if not root_volumes:
            return None
        return root_volumes[0]

    @staticmethod
    def get_by_uuid(uuid):
        db_obj = StateUpdateEvent.dbapi.get_state_update_event_by_uuid(uuid)
        return StateUpdateEvent.from_db_object(db_obj)

    @staticmethod
    def get_by_instance_uuid(instance_uuid):
        db_obj = StateUpdateEvent.dbapi.get_state_update_event_by_instance(
            instance_uuid
        )
        return StateUpdateEvent.from_db_object(db_obj)

    def create(self):
        values = {
            "instance_uuid": self.instance_uuid,
            "state_update": self.state_update,
            "image": self.image,
            "flavor": self.flavor,
            "handled": False,
        }
        db_obj = self.dbapi.create_state_update_event(values)
        self.uuid = db_obj.uuid
        self.refresh()

    def set_handled(self, handled=True):
        values = {"handled": handled}
        self.dbapi.update_instance_state_update_event(
            self.uuid, self.instance_uuid, values
        )
        self.refresh()

    def refresh(self):
        db_obj = StateUpdateEvent.get_by_uuid(self.uuid)
        new = StateUpdateEvent.from_db_object(db_obj)
        for field in self.fields:
            if hasattr(new, field):
                value = getattr(new, field)
                setattr(self, field, value)
        self.reset_changes()
