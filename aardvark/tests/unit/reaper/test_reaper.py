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

import aardvark.conf
from aardvark import exception
from aardvark.reaper import reaper
from aardvark.reaper import reaper_action as ra
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as obj_fakes
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class ReaperTests(base.TestCase):

    def setUp(self):
        super(ReaperTests, self).setUp()
        self.reaper = self._init_reaper()

    @mock.patch('aardvark.api.nova')
    @mock.patch('aardvark.api.placement')
    def _init_reaper(self, mock_placement, mock_novaclient):
        return reaper.Reaper()

    @mock.patch('aardvark.api.nova.server_rebuild')
    @mock.patch('aardvark.api.nova.server_reset_state')
    def test_handle_reaper_request(self, mock_reset, mock_rebuild):
        # create a request with no aggregates
        uuids = ['instance1', 'instance2']
        image = 'fake_image'
        request = fakes.make_reaper_request(uuids=uuids, image=image)
        with mock.patch.object(self.reaper, '_do_handle_reaper_request'):
            self.reaper.handle_reaper_request(request)
            mock_rebuild.assert_has_calls([
                mock.call('instance1', image), mock.call('instance2', image)
            ], any_order=True)
            self.assertTrue(not mock_reset.called)

    @mock.patch('aardvark.api.nova.server_rebuild')
    @mock.patch('aardvark.api.nova.server_reset_state')
    def test_handle_reaper_request_error(self, mock_reset, mock_rebuild):
        uuids = ['instance1', 'instance2']
        request = fakes.make_reaper_request(uuids=uuids)
        self.reaper.aggregates = ['aggregate_1']
        self.assertNotEqual(self.reaper.aggregates, request.aggregates)
        with mock.patch.object(self.reaper, '_do_handle_reaper_request') as m:
            m.side_effect = exception.PreemptibleRequest()
            self.assertRaises(exception.PreemptibleRequest,
                             self.reaper.handle_reaper_request, request)
            mock_reset.assert_has_calls([
                mock.call('instance1'), mock.call('instance2')
            ], any_order=True)
            self.assertTrue(not mock_rebuild.called)

    @mock.patch('aardvark.objects.system.System')
    def test_do_handle_reaper_request(self, system_mock):
        project_id = 'preemptible1'
        project = [mock.Mock(_id=project_id)]
        self.reaper.aggregates = ['aggregate_1']
        mocked_system = mock.Mock(preemptible_projects=project)
        system_mock.return_value = mocked_system
        request = fakes.make_reaper_request(project="project1")
        self.assertNotEqual(self.reaper.aggregates, request.aggregates)
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            self.reaper._do_handle_reaper_request(request)
            # Make sure that the request has the aggregates of the reaper
            # instance.
            self.assertEqual(self.reaper.aggregates, request.aggregates)
            mocked.assert_called_once()

    @mock.patch('aardvark.objects.system.System')
    def test_handle_state_calculation_request(self, system_mock):
        state_mock = mock.Mock(usage=mock.Mock(return_value=90))
        mocked_system = mock.Mock(
            system_state=mock.Mock(return_value=state_mock))
        system_mock.return_value = mocked_system
        CONF.aardvark.watermark = 80
        request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            with mock.patch.object(self.reaper, '_delete_locked_instances'):
                self.reaper.handle_state_calculation_request(request)
                self.assertTrue(mocked.called)

    @mock.patch('aardvark.objects.system.System')
    def test_handle_state_calculation_request_not_needed(self, system_mock):
        state_mock = mock.Mock(usage=mock.Mock(return_value=75))
        mocked_system = mock.Mock(
            system_state=mock.Mock(return_value=state_mock))
        system_mock.return_value = mocked_system
        CONF.aardvark.watermark = 80
        request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'free_resources') as mocked:
            with mock.patch.object(self.reaper, '_delete_locked_instances'):
                self.reaper.handle_state_calculation_request(request)
                self.assertTrue(not mocked.called)

    @mock.patch('aardvark.api.nova.server_delete')
    @mock.patch('aardvark.api.placement.get_consumer_allocations')
    def test_free_resources(self, mock_allocs, mock_delete):
        mock_projects = [mock.Mock(id_=1), mock.Mock(id_=2)]
        system = mock.Mock(preemptible_projects=mock_projects)
        request = fakes.make_reaper_request()
        hosts = ['host1']
        servers = [mock.Mock(uuid='server1'), mock.Mock(uuid='server2')]
        # Hack for mock's limitation with the name attribute
        for server in servers:
            server.name = server.uuid
        mocked_return = mock.Mock(return_value=(hosts, servers))
        not_found = obj_fakes.make_resources()
        mock_allocs.return_value = not_found
        mock_strategy = mock.Mock(get_preemptible_servers=mocked_return)
        with mock.patch.object(self.reaper, '_load_configured_strategy') as m:
            m.return_value = mock_strategy
            self.reaper.free_resources(request, system)
            mock_delete.assert_has_calls([
                mock.call('server1'), mock.call('server2')
            ], any_order=True)

    @mock.patch('aardvark.api.nova.server_delete')
    def test_free_resources_not_found_server(self, mock_delete):
        mock_projects = [mock.Mock(id_=1), mock.Mock(id_=2)]
        system = mock.Mock(preemptible_projects=mock_projects)
        request = fakes.make_reaper_request()
        mock_delete.side_effect = n_exc.NotFound("")
        hosts = ['host1']
        servers = [mock.Mock(uuid='server1'), mock.Mock(uuid='server2')]
        # Hack for mock's limitation with the name attribute
        for server in servers:
            server.name = server.uuid
        mocked_return = mock.Mock(return_value=(hosts, servers))
        mock_strategy = mock.Mock(get_preemptible_servers=mocked_return)
        with mock.patch.object(self.reaper, '_load_configured_strategy') as m:
            m.return_value = mock_strategy
            self.assertRaises(exception.RetriesExceeded,
                              self.reaper.free_resources, request, system)

    @mock.patch("aardvark.reaper.reaper_action.ReaperAction")
    def test_handle_request(self, reaper_action):
        reaper_request = fakes.make_reaper_request()
        calculation_request = fakes.make_calculation_request()
        with mock.patch.object(self.reaper, 'handle_reaper_request') as m:
            self.reaper.handle_request(reaper_request)
            m.assert_called_once_with(reaper_request)
        with mock.patch.object(
            self.reaper, 'handle_state_calculation_request') as m:
            self.reaper.handle_request(calculation_request)
            m.assert_called_once_with(calculation_request)

    def test_check_requested_aggregates(self):
        self.reaper.aggregates = []
        request = mock.Mock()
        request.aggregates = ['agg1', 'agg2', 'agg3']
        # No exception is raised
        self.reaper._check_requested_aggregates(request)

        self.reaper.aggregates = ['agg1', 'agg2', 'agg3', 'agg4']
        request.aggregates = ['agg1', 'agg2', 'agg3']
        # No exception is raised
        self.reaper._check_requested_aggregates(request)
        self.assertEqual(['agg1', 'agg2', 'agg3'], sorted(request.aggregates))

        self.reaper.aggregates = ['agg4']
        request.aggregates = ['agg1', 'agg2', 'agg3']
        self.assertRaises(exception.UnwatchedAggregate,
                          self.reaper._check_requested_aggregates, request)

        self.reaper.aggregates = [1, 2, 3, 4]
        request.aggregates = [0, 3, 2]
        self.reaper._check_requested_aggregates(request)
        self.assertEqual([2, 3], sorted(request.aggregates))

        self.reaper.aggregates = [2, 8]
        request.aggregates = [3, 2, 5]
        self.reaper._check_requested_aggregates(request)
        self.assertEqual([2], sorted(request.aggregates))

        self.reaper.aggregates = ['agg4']
        request.aggregates = []
        self.reaper._check_requested_aggregates(request)

    @mock.patch('aardvark.api.placement.get_consumer_allocations')
    def test_wait_until_allocations_are_deleted(self, mock_allocs):
        server1 = mock.Mock(uuid='uuid1', rp_uuid='rp1_uuid')
        server2 = mock.Mock(uuid='uuid2', rp_uuid='rp2_uuid')
        servers = [server1, server2]
        mock_allocs.side_effect = [
            obj_fakes.make_resources(),
            obj_fakes.make_resources(vcpu=1),
            obj_fakes.make_resources(),
        ]
        self.reaper.wait_until_allocations_are_deleted(servers)
        self.assertEqual([], servers)

        servers = [server1, server2]
        mock_allocs.side_effect = [
            obj_fakes.make_resources(),
            obj_fakes.make_resources(vcpu=1),
            obj_fakes.make_resources(vcpu=1),
            obj_fakes.make_resources(vcpu=1),
        ]
        with mock.patch('time.time') as mocked_time:
            mocked_time.side_effect = [1, 1, 1, 1, 100]
            self.reaper.wait_until_allocations_are_deleted(servers)
            self.assertEqual([server2], servers)

    @mock.patch("aardvark.reaper.reaper_action.ReaperAction")
    def test_handle_request_preemptible_request(self, reaper_action):
        mock_action = mock.Mock()
        reaper_action.return_value = mock_action
        reaper_request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'handle_reaper_request') as m:
            m.side_effect = exception.PreemptibleRequest()
            self.reaper.handle_request(reaper_request)
        self.assertEqual(ra.ActionState.CANCELED, mock_action.state)

    @mock.patch("aardvark.reaper.reaper_action.ReaperAction")
    def test_handle_request_unexpected_error(self, reaper_action):
        mock_action = mock.Mock()
        reaper_action.return_value = mock_action
        reaper_request = fakes.make_reaper_request()
        with mock.patch.object(self.reaper, 'handle_reaper_request') as m:
            reason = "unexpected error"
            m.side_effect = Exception(reason)
            self.reaper.handle_request(reaper_request)
        self.assertEqual(ra.ActionState.FAILED, mock_action.state)
