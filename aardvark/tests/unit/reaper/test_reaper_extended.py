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
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class ReaperExtendedTests(base.TestCase):
    def setUp(self):
        super().setUp()
        self.reaper = self._init_reaper()

    @mock.patch("aardvark.api.nova")
    @mock.patch("aardvark.api.placement")
    def _init_reaper(self, mock_placement, mock_novaclient):
        return reaper.Reaper()

    @mock.patch("aardvark.api.nova.server_delete")
    def test_delete_instance_success(self, mock_delete):
        mock_delete.return_value = True
        server = mock.Mock(uuid="server1", name="server-name")
        self.reaper._delete_instance(server)
        mock_delete.assert_called_once_with("server1")

    @mock.patch("aardvark.api.nova.server_delete")
    def test_delete_instance_not_found_no_side_effect(self, mock_delete):
        mock_delete.side_effect = n_exc.NotFound("")
        server = mock.Mock(uuid="server1", name="server-name")
        # Should not raise when no side_effect configured
        self.reaper._delete_instance(server)

    @mock.patch("aardvark.api.nova.server_delete")
    def test_delete_instance_not_found_with_side_effect(self, mock_delete):
        mock_delete.side_effect = n_exc.NotFound("")
        server = mock.Mock(uuid="server1", name="server-name")
        self.assertRaises(
            exception.RetryException,
            self.reaper._delete_instance,
            server,
            side_effect=exception.RetryException,
        )

    @mock.patch("aardvark.api.nova.server_delete")
    def test_delete_instance_notifies(self, mock_delete):
        mock_delete.return_value = True
        server = mock.Mock(uuid="server1", name="server-name")
        mock_notifier = mock.Mock()
        self.reaper.notifiers = [mock_notifier]
        self.reaper._delete_instance(server)
        mock_notifier.notify_about_instance.assert_called_once_with(server)

    def test_notify_about_instance(self):
        mock_notifier = mock.Mock()
        self.reaper.notifiers = [mock_notifier]
        instance = mock.Mock(uuid="inst-uuid")
        self.reaper.notify_about_instance(instance)
        mock_notifier.notify_about_instance.assert_called_once_with(instance)

    def test_notify_about_instance_error_continues(self):
        mock_notifier = mock.Mock()
        mock_notifier.notify_about_instance.side_effect = Exception("error")
        self.reaper.notifiers = [mock_notifier]
        instance = mock.Mock(uuid="inst-uuid")
        # Should not raise
        self.reaper.notify_about_instance(instance)

    def test_notify_about_action(self):
        mock_notifier = mock.Mock()
        self.reaper.notifiers = [mock_notifier]
        action = mock.Mock(uuid="action-uuid")
        self.reaper.notify_about_action(action)
        mock_notifier.notify_about_action.assert_called_once_with(action)

    def test_notify_about_action_error_continues(self):
        mock_notifier = mock.Mock()
        mock_notifier.notify_about_action.side_effect = Exception("error")
        self.reaper.notifiers = [mock_notifier]
        action = mock.Mock(uuid="action-uuid")
        # Should not raise
        self.reaper.notify_about_action(action)

    def test_stop_handling(self):
        self.reaper.flag = True
        self.reaper.stop_handling()
        self.assertFalse(self.reaper.flag)

    @mock.patch("aardvark.api.nova.server_rebuild")
    def test_rebuild_instances(self, mock_rebuild):
        self.reaper._rebuild_instances(["uuid1", "uuid2"], "image-uuid")
        mock_rebuild.assert_any_call("uuid1", "image-uuid")
        mock_rebuild.assert_any_call("uuid2", "image-uuid")

    @mock.patch("aardvark.api.nova.server_rebuild")
    def test_rebuild_instances_not_found(self, mock_rebuild):
        mock_rebuild.side_effect = n_exc.NotFound("")
        # Should not raise
        self.reaper._rebuild_instances(["uuid1"], "image-uuid")

    @mock.patch("aardvark.api.nova.server_reset_state")
    def test_reset_instances(self, mock_reset):
        self.reaper._reset_instances(["uuid1", "uuid2"])
        mock_reset.assert_any_call("uuid1")
        mock_reset.assert_any_call("uuid2")

    @mock.patch("aardvark.api.nova.server_reset_state")
    def test_reset_instances_not_found(self, mock_reset):
        mock_reset.side_effect = n_exc.NotFound("")
        # Should not raise
        self.reaper._reset_instances(["uuid1"])

    @mock.patch("aardvark.objects.system.System")
    def test_handle_old_instance_request(self, mock_system):
        mock_system_instance = mock.Mock()
        mock_system_instance.preemptible_projects = []
        mock_system_instance.preemptible_flavors = []
        mock_system.return_value = mock_system_instance
        request = fakes.make_calculation_request()
        with mock.patch.object(self.reaper, "_delete_locked_instances"):
            result = self.reaper.handle_old_instance_request(request)
        self.assertEqual([], result)

    @mock.patch("aardvark.objects.instance.InstanceList")
    @mock.patch("aardvark.objects.system.System")
    def test_handle_old_instance_request_with_old_instances(
        self, mock_system, mock_instance_list
    ):
        CONF.aardvark.max_life_span = 3600  # 1 hour
        mock_project = mock.Mock(id_="proj-uuid")
        mock_system_instance = mock.Mock()
        mock_system_instance.preemptible_projects = [mock_project]
        mock_system_instance.preemptible_flavors = []
        mock_system.return_value = mock_system_instance

        mock_instance = mock.Mock(
            uuid="inst-uuid",
            created="2019-01-01T00:00:00Z",
        )
        mock_instance_list.return_value.instances.return_value = [
            mock_instance
        ]

        with mock.patch("aardvark.utils.seconds_since", return_value=7200):
            with mock.patch.object(self.reaper, "_delete_locked_instances"):
                with mock.patch.object(
                    self.reaper, "_delete_instance"
                ) as mock_del:
                    self.reaper.handle_old_instance_request(request=None)
                    mock_del.assert_called_once()

    @mock.patch("aardvark.objects.instance.InstanceList")
    @mock.patch("aardvark.objects.system.System")
    def test_delete_locked_instances(self, mock_system, mock_instance_list):
        mock_project = mock.Mock(id_="proj-uuid")
        mock_system_instance = mock.Mock()
        mock_system_instance.preemptible_projects = [mock_project]
        mock_system_instance.preemptible_flavors = []
        mock_system.return_value = mock_system_instance

        mock_instance = mock.Mock(uuid="locked-uuid")
        mock_instance_list.return_value.instances.return_value = [
            mock_instance
        ]

        with mock.patch.object(self.reaper, "_delete_instance") as mock_del:
            self.reaper._delete_locked_instances(mock_system_instance)
            mock_del.assert_called_once_with(mock_instance)

    @mock.patch("aardvark.objects.instance.InstanceList")
    @mock.patch("aardvark.objects.system.System")
    def test_delete_locked_instances_with_flavors(
        self, mock_system, mock_instance_list
    ):
        mock_flavor = mock.Mock(id="flavor-uuid")
        mock_system_instance = mock.Mock()
        mock_system_instance.preemptible_projects = []
        mock_system_instance.preemptible_flavors = [mock_flavor]
        mock_system.return_value = mock_system_instance

        mock_instance = mock.Mock(uuid="locked-uuid")
        mock_instance_list.return_value.instances.return_value = [
            mock_instance
        ]

        with mock.patch.object(self.reaper, "_delete_instance") as mock_del:
            self.reaper._delete_locked_instances(mock_system_instance)
            mock_del.assert_called_once_with(mock_instance)

    @mock.patch("aardvark.objects.system.System")
    def test_handle_state_calculation_retries_exceeded(self, mock_system):
        state_mock = mock.Mock(usage=mock.Mock(return_value=90))
        mocked_system = mock.Mock(
            system_state=mock.Mock(return_value=state_mock)
        )
        mock_system.return_value = mocked_system
        CONF.aardvark.watermark = 80
        request = fakes.make_calculation_request()
        with mock.patch.object(self.reaper, "free_resources") as mocked:
            with mock.patch.object(self.reaper, "_delete_locked_instances"):
                mocked.side_effect = exception.RetriesExceeded("msg")
                # Should not raise
                self.reaper.handle_state_calculation_request(request)

    @mock.patch("aardvark.reaper.reaper_action.ReaperAction")
    def test_handle_request_old_instance(self, reaper_action):
        from aardvark.reaper.reaper_request import OldInstanceKillerRequest

        mock_action = mock.Mock()
        reaper_action.return_value = mock_action
        killer_request = OldInstanceKillerRequest()
        with mock.patch.object(
            self.reaper, "handle_old_instance_request"
        ) as m:
            m.return_value = []
            self.reaper.handle_request(killer_request)
            m.assert_called_once_with(killer_request)


class ReaperWhileRunningTests(base.TestCase):
    def test_while_running_decorator(self):
        """Test the while_running decorator stops when flag is False"""
        calls = []

        @reaper.while_running
        def mock_fn(self, board):
            calls.append(1)
            self.flag = False

        mock_self = mock.Mock()
        mock_self.flag = True
        mock_fn(mock_self, mock.Mock())
        self.assertEqual(1, len(calls))
