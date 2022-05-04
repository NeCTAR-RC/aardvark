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

from novaclient import exceptions as n_exc

from aardvark import exception
from aardvark.notifications import base as base_obj
from aardvark.notifications import endpoints
from aardvark.notifications import events
from aardvark.reaper import reaper_action as ra
from aardvark.tests.unit.db import base
from aardvark.tests.unit.notifications import fakes


class EndpointsTests(base.DbTestCase):

    def setUp(self):
        super(EndpointsTests, self).setUp()
        self.endpoint = base_obj.NotificationEndpoint()

    def _assert_default_action(self, noop_args, result):
        default_action = self.endpoint._default_action(*noop_args)
        self.assertEqual(default_action, result)

    def _get_noop_payload(self):
        return {}

    def test_default_action(self):
        noop_payload = self._get_noop_payload()
        noops = [None, None, None, noop_payload, None]
        self._assert_default_action(noops, self.endpoint.audit(*noops))
        self._assert_default_action(noops, self.endpoint.critical(*noops))
        self._assert_default_action(noops, self.endpoint.debug(*noops))
        self._assert_default_action(noops, self.endpoint.error(*noops))
        self._assert_default_action(noops, self.endpoint.info(*noops))
        self._assert_default_action(noops, self.endpoint.sample(*noops))
        self._assert_default_action(noops, self.endpoint.warn(*noops))


class SchedulingEndpointTests(EndpointsTests):

    def setUp(self):
        super(SchedulingEndpointTests, self).setUp()
        self.endpoint = endpoints.SchedulingEndpoint()

    def _get_noop_payload(self):
        return fakes.make_scheduling_payload([], None)

    def test_error_payload(self):
        instances = ['instance_uuid']
        aggregates = ['aggregate']
        sched_payload = fakes.make_scheduling_payload(instances, aggregates)
        self.endpoint.error(None, None, None, sched_payload, None)

    def test_error_payload_multiple_instances(self):
        instances = ['instance_uuid1', 'instance_uuid2']
        aggregates = ['aggregate']
        sched_payload = fakes.make_scheduling_payload(instances, aggregates)
        self.endpoint.error(None, None, None, sched_payload, None)
        event = events.SchedulingEvent.get_by_instance_uuid('instance_uuid1')
        self.assertEqual(2, event.count_scheduling_instances(handled=False))

    def test_error_payload_no_aggregates(self):
        instances = ['instance_uuid1', 'instance_uuid2']
        sched_payload = fakes.make_scheduling_payload(instances)
        self.endpoint.error(None, None, None, sched_payload, None)
        event = events.SchedulingEvent.get_by_instance_uuid('instance_uuid1')
        self.assertEqual(2, event.count_scheduling_instances(handled=False))


class StateUpdateEndpointTests(EndpointsTests):

    def setUp(self):
        super(StateUpdateEndpointTests, self).setUp()
        self.endpoint = self._init_mocked_endpoint()

    def _get_noop_payload(self):
        return fakes.make_state_update_payload(
            None, "ok", "not_ok", None, None)

    @mock.patch('aardvark.api.nova')
    @mock.patch('aardvark.reaper.job_manager.JobManager')
    def _init_mocked_endpoint(self, mock_job_manager, mock_novaclient):
        self.mocked_nova = mock_novaclient
        self.mocked_job_manager = mock_job_manager
        return endpoints.StateUpdateEndpoint()

    def test_handled_on_missing_scheduling_info(self):
        instance = "instance_uuid"
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"

        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)

        mock_reset = mock.Mock()
        self.endpoint._reset_instances = mock_reset
        with mock.patch.object(self.endpoint, 'trigger_reaper') as trigger:
            trigger.side_effect = exception.RetriesExceeded
            action = self.endpoint.info(None, None, None, payload, None)
            self.assertEqual(self.endpoint.handled(), action)
            mock_reset.assert_called_once_with([instance])

    def test_not_to_pending(self):
        instance = "instance_uuid"
        new_state = "error"
        old_state = "scheduling"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"

        update_payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)

        with mock.patch.object(self.endpoint, 'trigger_reaper') as trigger:
            self.endpoint.info(None, None, None, update_payload, None)
            self.assertTrue(not trigger.called)

    def test_payload_build_to_pending(self):
        instance = "instance_uuid"
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"
        e_type = ra.ActionEvent.BUILD_REQUEST

        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)

        flavor = payload['nova_object.data']['flavor']['nova_object.data']

        with mock.patch.object(self.endpoint, 'trigger_reaper') as trigger:
            self.endpoint.info(None, None, None, payload, None)
            trigger.assert_called_once_with(
                instance, flavor, image_uuid, e_type, False)

    def test_payload_rebuild_to_pending(self):
        instance = "instance_uuid"
        new_state = "pending"
        old_state = "whatever"
        old_task = "rebuilding"
        new_task = None
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"
        e_type = ra.ActionEvent.REBUILD_REQUEST

        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid,
            old_task=old_task, new_task=new_task)

        flavor = payload['nova_object.data']['flavor']['nova_object.data']

        with mock.patch.object(self.endpoint, 'trigger_reaper') as trigger:
            self.endpoint.info(None, None, None, payload, None)
            trigger.assert_called_once_with(
                instance, flavor, image_uuid, e_type, False)

    def test_trigger_reaper(self):
        instance = "instance_uuid"
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"
        aggs = ['agg1']
        e_type = ra.ActionEvent.BUILD_REQUEST

        scheduling_payload = fakes.make_scheduling_payload([instance],
                                                           aggregates=aggs)
        scheduling_event = events.SchedulingEvent.from_payload(
            scheduling_payload)
        scheduling_event.create()
        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)
        flavor = payload['nova_object.data']['flavor']['nova_object.data']

        self.endpoint.trigger_reaper(instance, flavor, image_uuid, e_type)
        self.assertTrue(self.endpoint.job_manager.post_job.called)
        self.assertEqual(0, scheduling_event.count_scheduling_instances())

    def test_trigger_reaper_multiple_instances(self):
        instances = ["instance_uuid1", "instance_uuid2"]
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"
        request_id = 123
        aggs = ['agg1', 'agg2']
        e_type = ra.ActionEvent.BUILD_REQUEST

        scheduling_payload = fakes.make_scheduling_payload(instances,
                                                           req_id=request_id,
                                                           aggregates=aggs)
        scheduling_event = events.SchedulingEvent.from_payload(
            scheduling_payload)
        payload = fakes.make_state_update_payload(
            instances, new_state, old_state, image_uuid, flavor_uuid)
        scheduling_event.create()
        flavor = payload['nova_object.data']['flavor']['nova_object.data']

        self.endpoint.trigger_reaper(instances[0], flavor, image_uuid, e_type)
        self.assertTrue(not self.endpoint.job_manager.post_job.called)

        self.endpoint.trigger_reaper(instances[1], flavor, image_uuid, e_type)
        self.endpoint.job_manager.post_job.assert_called_once()
        self.assertEqual(0, scheduling_event.count_scheduling_instances())

    @mock.patch('aardvark.api.nova.aggregate_list')
    @mock.patch('aardvark.api.nova.server_reset_state')
    def test_trigger_reaper_failure(self, mock_reset, mock_list):
        instance = "instance_uuid"
        new_state = "pending"
        old_state = "building"
        image_uuid = "image_uuid"
        flavor_uuid = "flavor_uuid"
        event_type = ra.ActionEvent.BUILD_REQUEST

        scheduling_payload = fakes.make_scheduling_payload([instance])
        scheduling_event = events.SchedulingEvent.from_payload(
            scheduling_payload)
        scheduling_event.create()
        payload = fakes.make_state_update_payload(
            instance, new_state, old_state, image_uuid, flavor_uuid)
        flavor = payload['nova_object.data']['flavor']['nova_object.data']

        self.endpoint.job_manager.post_job.side_effect = \
            exception.ReaperException()
        self.endpoint.trigger_reaper(instance, flavor, image_uuid, event_type)
        mock_reset.assert_called_once_with(instance)
        self.assertEqual(0, scheduling_event.count_scheduling_instances())

    @mock.patch('aardvark.api.nova.server_reset_state')
    def test_reset_instances(self, mock_reset):
        mock_reset.side_effect = n_exc.NotFound("")
        instance = ["instance_uuid"]
        try:
            self.endpoint._reset_instances(instance)
            self.assertTrue(True)
        except Exception:
            self.assertTrue(False)
