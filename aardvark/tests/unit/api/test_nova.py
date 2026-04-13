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

from aardvark.api import nova
import aardvark.conf
from aardvark.tests import base


CONF = aardvark.conf.CONF


class NovaClientTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def _make_nova_client(self):
        mock_client = mock.Mock()
        return mock_client

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_powering_off(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "ACTIVE"
        mock_client.servers.get.return_value = mock_server
        # Patch getattr to return "powering-off" for the task_state attribute
        original_getattr = getattr

        def patched_getattr(obj, name, *args):
            if obj is mock_server and name == "OS-EXT-STS:task_state":
                return "powering-off"
            return original_getattr(obj, name, *args)

        with mock.patch(
            "aardvark.api.nova.getattr", side_effect=patched_getattr
        ):
            result = nova.server_delete("fake-uuid")
        self.assertFalse(result)

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_error_status(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "ERROR"
        mock_client.servers.get.return_value = mock_server
        # Override getattr for task_state
        with mock.patch(
            "aardvark.api.nova.getattr",
            create=True,
            side_effect=lambda obj, name, *a: "not-powering-off",
        ):
            result = nova.server_delete("fake-uuid")
        self.assertTrue(result)
        mock_server.delete.assert_called_once()

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_shutoff_status(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "SHUTOFF"
        mock_client.servers.get.return_value = mock_server
        with mock.patch(
            "aardvark.api.nova.getattr",
            create=True,
            side_effect=lambda obj, name, *a: "not-powering-off",
        ):
            result = nova.server_delete("fake-uuid")
        self.assertTrue(result)
        mock_server.unlock.assert_called_once()
        mock_server.delete.assert_called_once()

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_shutoff_unlock_exception(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "SHUTOFF"
        mock_server.unlock.side_effect = Exception("unlock error")
        mock_client.servers.get.return_value = mock_server
        with mock.patch(
            "aardvark.api.nova.getattr",
            create=True,
            side_effect=lambda obj, name, *a: "not-powering-off",
        ):
            result = nova.server_delete("fake-uuid")
        self.assertTrue(result)
        mock_server.delete.assert_called_once()

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_active_status(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "ACTIVE"
        mock_client.servers.get.return_value = mock_server
        CONF.compute.client_version = "2.73"
        with mock.patch(
            "aardvark.api.nova.getattr",
            create=True,
            side_effect=lambda obj, name, *a: None,
        ):
            result = nova.server_delete("fake-uuid")
        self.assertFalse(result)
        mock_server.stop.assert_called_once()
        mock_server.lock.assert_called_once()

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_delete_active_old_client(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_server = mock.Mock()
        mock_server.id = "fake-uuid"
        mock_server.status = "ACTIVE"
        mock_client.servers.get.return_value = mock_server
        CONF.compute.client_version = "2.1"
        with mock.patch(
            "aardvark.api.nova.getattr",
            create=True,
            side_effect=lambda obj, name, *a: None,
        ):
            result = nova.server_delete("fake-uuid")
        self.assertFalse(result)
        mock_server.stop.assert_called_once()
        mock_server.lock.assert_called_once_with()

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_rebuild(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        nova.server_rebuild("server-uuid", "image-uuid")
        mock_client.servers.rebuild.assert_called_once_with(
            "server-uuid", "image-uuid"
        )

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_reset_state(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        nova.server_reset_state("server-uuid")
        mock_client.servers.reset_state.assert_called_once_with("server-uuid")

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_server_list(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.servers.list.return_value = ["server1", "server2"]
        result = nova.server_list(project_id="proj1")
        mock_client.servers.list.assert_called_once_with(
            search_opts={"project_id": "proj1"}
        )
        self.assertEqual(["server1", "server2"], result)

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_aggregate_list(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.aggregates.list.return_value = ["agg1", "agg2"]
        result = nova.aggregate_list()
        self.assertEqual(["agg1", "agg2"], result)

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_service_status(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_service = mock.Mock()
        mock_client.services.list.return_value = [mock_service]
        result = nova.service_status("host1")
        mock_client.services.list.assert_called_once_with(
            "host1", "nova-compute"
        )
        self.assertEqual(mock_service, result)

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_hypervisor_get(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_hv = mock.Mock()
        mock_client.hypervisors.get.return_value = mock_hv
        result = nova.hypervisor_get("hv-uuid")
        mock_client.hypervisors.get.assert_called_once_with("hv-uuid")
        self.assertEqual(mock_hv, result)

    @mock.patch("aardvark.api.nova._get_nova_client")
    def test_get_preemptible_flavors(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        flavor1 = mock.Mock()
        flavor1.get_keys.return_value = {"flavor_class:name": "preemptible"}
        flavor2 = mock.Mock()
        flavor2.get_keys.return_value = {"flavor_class:name": "other"}
        mock_client.flavors.list.return_value = [flavor1, flavor2]
        result = nova.get_preemptible_flavors()
        self.assertEqual([flavor1], result)
