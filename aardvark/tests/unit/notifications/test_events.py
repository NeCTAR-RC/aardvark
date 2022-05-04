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


from unittest import mock

from aardvark.notifications import events
from aardvark.tests import base
from aardvark.tests.unit.notifications import fakes


class EventTests(base.TestCase):

    def setUp(self):
        super(EventTests, self).setUp()


class SchedulingEventTests(EventTests):

    def setUp(self):
        super(SchedulingEventTests, self).setUp()

    def test_scheduling_event(self):
        instances = ["instance_uuid1", "instance_uuid2"]
        aggs = ["agg1", "agg2"]
        request_id = 123
        project = "project"
        payload = fakes.make_scheduling_payload(
            instances, aggregates=aggs, req_id=request_id, project=project)
        event = events.SchedulingEvent.from_payload(payload)
        self.assertEqual(instances, event.instance_uuids)
        self.assertEqual(aggs, event.aggregates)
        self.assertEqual(request_id, event.request_id)
        self.assertEqual(project, event.project_id)
        self.assertTrue(event.multiple_instances)

    @mock.patch('aardvark.utils.get_default_aggregates')
    def test_scheduling_event_no_aggregates(self, mock_aggs):
        mock_aggs.return_value = []
        instances = ["instance_uuid1"]
        payload = fakes.make_scheduling_payload(instances)
        event = events.SchedulingEvent.from_payload(payload)
        self.assertEqual(instances, event.instance_uuids)
        self.assertEqual(0, len(event.aggregates))
        self.assertTrue(not event.multiple_instances)


class InstanceUpdateEventTests(EventTests):

    def setUp(self):
        super(InstanceUpdateEventTests, self).setUp()

    def test_instance_update_event(self):
        instance = "instance_uuid1"
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"

        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)
        event = events.StateUpdateEvent.from_payload(payload)
        self.assertEqual(instance, event.instance_uuid)
        self.assertEqual(new_state, event.new_state)
        self.assertEqual(old_state, event.old_state)
        self.assertEqual(image_uuid, event.image)
        self.assertEqual(flavor_uuid, event.flavor["uuid"])
