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

from aardvark.db import api as db_api
from aardvark import exception
from aardvark.notifications import events
from aardvark.tests.unit.db import base
from aardvark.tests.unit.notifications import fakes


class SchedulingEventDBTests(base.DbTestCase):
    def _create_scheduling_event(
        self, instance_uuids=None, req_id=1, aggregates=None
    ):
        instance_uuids = instance_uuids or ["instance-uuid"]
        payload = fakes.make_scheduling_payload(
            instance_uuids, aggregates=aggregates, req_id=req_id
        )
        event = events.SchedulingEvent.from_payload(payload)
        event.create()
        return event

    def test_create_scheduling_event(self):
        event = self._create_scheduling_event()
        self.assertIsNotNone(event.uuid)

    def test_create_scheduling_event_duplicate(self):
        # Creating the same scheduling event twice should handle
        # SchedulingEventAlreadyExists without raising
        self._create_scheduling_event(req_id=999)
        # Second call with same req_id — should not raise
        self._create_scheduling_event(req_id=999)

    def test_get_instance_scheduling_event(self):
        dbapi = db_api.get_instance()
        instance_uuid = "test-get-instance-uuid"
        self._create_scheduling_event(
            instance_uuids=[instance_uuid], req_id=111
        )
        result = dbapi.get_instance_scheduling_event(instance_uuid)
        self.assertEqual(instance_uuid, result.instance_uuid)

    def test_get_instance_scheduling_event_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.SchedulingEventNotFound,
            dbapi.get_instance_scheduling_event,
            "not-existing-uuid",
        )

    def test_get_scheduling_event_by_request_id(self):
        dbapi = db_api.get_instance()
        self._create_scheduling_event(req_id=222)
        result = dbapi.get_scheduling_event_by_request_id(222)
        self.assertEqual(222, result.request_id)

    def test_get_scheduling_event_by_request_id_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.SchedulingEventNotFound,
            dbapi.get_scheduling_event_by_request_id,
            "not-existing",
        )

    def test_list_scheduling_event_instances(self):
        dbapi = db_api.get_instance()
        event = self._create_scheduling_event(
            instance_uuids=["inst1", "inst2"], req_id=333
        )
        instances = dbapi.list_scheduling_event_instances(event.uuid)
        self.assertEqual(2, len(instances))

    def test_update_scheduling_event(self):
        dbapi = db_api.get_instance()
        event = self._create_scheduling_event(req_id=444)
        dbapi.update_scheduling_event(event.uuid, {"retries": 2})
        result = dbapi.get_scheduling_event_by_request_id(444)
        self.assertEqual(2, result.retries)

    def test_update_scheduling_event_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.SchedulingEventNotFound,
            dbapi.update_scheduling_event,
            "not-existing-uuid",
            {"retries": 1},
        )

    def test_update_instance_scheduling_event(self):
        dbapi = db_api.get_instance()
        instance_uuid = "inst-update-uuid"
        event = self._create_scheduling_event(
            instance_uuids=[instance_uuid], req_id=555
        )
        dbapi.update_instance_scheduling_event(
            event.uuid, {"handled": True}, instance_uuid=instance_uuid
        )
        result = dbapi.get_instance_scheduling_event(
            instance_uuid, handled=True
        )
        self.assertTrue(result.handled)

    def test_count_instance_scheduling_events(self):
        dbapi = db_api.get_instance()
        event = self._create_scheduling_event(
            instance_uuids=["count-inst1", "count-inst2"], req_id=666
        )
        count = dbapi.count_instance_scheduling_events(
            event.uuid, handled=False
        )
        self.assertEqual(2, count)

    def test_create_state_update_event(self):
        dbapi = db_api.get_instance()
        values = {
            "instance_uuid": "state-inst-uuid",
            "state_update": {
                "nova_object.data": {
                    "state": "pending",
                    "old_state": "building",
                    "new_task_state": None,
                    "old_task_state": None,
                }
            },
            "image": "image-uuid",
            "flavor": {"vcpus": 2},
            "handled": False,
        }
        result = dbapi.create_state_update_event(values)
        self.assertIsNotNone(result.uuid)

    def test_create_state_update_event_duplicate(self):
        dbapi = db_api.get_instance()
        values = {
            "uuid": "dup-state-uuid",
            "instance_uuid": "dup-state-inst-uuid",
            "state_update": {"nova_object.data": {}},
            "image": "image-uuid",
            "flavor": {"vcpus": 2},
            "handled": False,
        }
        dbapi.create_state_update_event(values)
        self.assertRaises(
            exception.StateUpdateEventAlreadyExists,
            dbapi.create_state_update_event,
            values,
        )

    def test_get_state_update_event_by_instance(self):
        dbapi = db_api.get_instance()
        instance_uuid = "get-by-inst-uuid"
        values = {
            "instance_uuid": instance_uuid,
            "state_update": {"nova_object.data": {}},
            "image": "image-uuid",
            "flavor": {"vcpus": 2},
            "handled": False,
        }
        dbapi.create_state_update_event(values)
        result = dbapi.get_state_update_event_by_instance(instance_uuid)
        self.assertEqual(instance_uuid, result.instance_uuid)

    def test_get_state_update_event_by_instance_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.StateUpdateEventNotFound,
            dbapi.get_state_update_event_by_instance,
            "not-existing",
        )

    def test_get_state_update_event_by_uuid(self):
        dbapi = db_api.get_instance()
        values = {
            "uuid": "get-by-uuid-state",
            "instance_uuid": "some-inst-uuid",
            "state_update": {"nova_object.data": {}},
            "image": "image-uuid",
            "flavor": {"vcpus": 2},
            "handled": False,
        }
        dbapi.create_state_update_event(values)
        result = dbapi.get_state_update_event_by_uuid("get-by-uuid-state")
        self.assertEqual("get-by-uuid-state", result.uuid)

    def test_get_state_update_event_by_uuid_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.StateUpdateEventNotFound,
            dbapi.get_state_update_event_by_uuid,
            "not-existing",
        )

    def test_update_instance_state_update_event(self):
        dbapi = db_api.get_instance()
        instance_uuid = "upd-state-inst-uuid"
        values = {
            "instance_uuid": instance_uuid,
            "state_update": {"nova_object.data": {}},
            "image": "image-uuid",
            "flavor": {"vcpus": 2},
            "handled": False,
        }
        created = dbapi.create_state_update_event(values)
        dbapi.update_instance_state_update_event(
            created.uuid, instance_uuid, {"handled": True}
        )
        result = dbapi.get_state_update_event_by_uuid(created.uuid)
        self.assertTrue(result.handled)

    def test_update_instance_state_update_event_not_found(self):
        dbapi = db_api.get_instance()
        self.assertRaises(
            exception.StateUpdateEventNotFound,
            dbapi.update_instance_state_update_event,
            "not-existing",
            "inst-uuid",
            {"handled": True},
        )

    def test_list_reaper_actions(self):
        from aardvark.tests.unit.db import utils

        utils.create_test_reaper_action(uuid="list-action-uuid1")
        dbapi = db_api.get_instance()
        result = dbapi.list_reaper_actions()
        uuids = [r.uuid for r in result]
        self.assertIn("list-action-uuid1", uuids)
