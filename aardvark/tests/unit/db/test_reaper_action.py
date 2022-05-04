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
from aardvark.reaper import reaper_action as ra
from aardvark.tests.unit.db import base
from aardvark.tests.unit.db import utils


class ReaperActionTests(base.DbTestCase):

    def test_create_reaper_action(self):
        utils.create_test_reaper_action()

    def test_create_reaper_action_state_calculation(self):
        utils.create_test_reaper_action(event="STATE_CALCULATION")

    def test_create_reaper_action_rebuild(self):
        utils.create_test_reaper_action(event="REBUILD_REQUEST")

    def test_create_reaper_action_duplicate(self):
        utils.create_test_reaper_action()
        self.assertRaises(exception.ReaperActionAlreadyExists,
                          utils.create_test_reaper_action)

    def test_reaper_action_update(self):
        action = utils.create_test_reaper_action(state="ONGOING")
        values = {'state': "SUCCESS"}
        dbapi = db_api.get_instance()
        dbapi.update_reaper_action(action.uuid, values)
        new = ra.ReaperAction.get_by_uuid(action.uuid)
        self.assertEqual(ra.ActionState.SUCCESS, new.state)

    def test_reaper_action_update_not_found(self):
        values = {'state': "SUCCESS"}
        dbapi = db_api.get_instance()
        self.assertRaises(exception.ReaperActionNotFound,
                          dbapi.update_reaper_action, 'not-existing', values)

    def test_reaper_action_get_by_uuid(self):
        uuid = 'fake-uuid'
        action = utils.create_test_reaper_action(uuid=uuid)
        new = ra.ReaperAction.get_by_uuid(uuid)
        self.assertEqual(action.uuid, new.uuid)

    def test_reaper_action_get_by_instance_uuid(self):
        requested = 'fake-instance-uuid'
        uuid1 = 'fake-action-uuid1'
        uuid2 = 'fake-action-uuid2'
        utils.create_test_reaper_action(
            uuid=uuid1, requested_instances=[requested])
        utils.create_test_reaper_action(
            uuid=uuid2, requested_instances=[requested])
        results = ra.ReaperAction.get_by_instance_uuid(requested)
        result_uuids = [res.uuid for res in results]
        self.assertIn(uuid1, result_uuids)
        self.assertIn(uuid2, result_uuids)
        self.assertEqual(2, len(result_uuids))

    def test_reaper_action_get_by_victim(self):
        victim = 'fake-victim-uuid'
        act = utils.create_test_reaper_action(victims=[victim])
        results = ra.ReaperAction.get_by_victim_uuid(victim)
        for result in results:
            self.assertEqual(act.uuid, result.uuid)

    def test_reaper_action_get_by_uuid_not_found(self):
        self.assertRaises(exception.ReaperActionNotFound,
                          ra.ReaperAction.get_by_uuid, 'not-existing')

    def test_reaper_action_get_by_instance_uuid_not_found(self):
        self.assertEqual([], ra.ReaperAction.get_by_instance_uuid('not-there'))

    def test_reaper_action_get_by_victim_not_found(self):
        self.assertEqual([], ra.ReaperAction.get_by_victim_uuid('not-there'))
