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

from aardvark.objects import resource_provider
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


class ResourceProviderTests(base.TestCase):
    def setUp(self):
        super().setUp()
        self.rp = object_fakes.make_resource_provider(
            uuid="rp-uuid", name="rp1"
        )

    def test_init(self):
        rp = resource_provider.ResourceProvider("uuid1", "name1")
        self.assertEqual("uuid1", rp.uuid)
        self.assertEqual("name1", rp.name)
        self.assertEqual(0, rp.reserved_spots)
        self.assertFalse(rp.populated)

    def test_preemptible_servers_setter(self):
        server1 = object_fakes.make_server(uuid="s1")
        server1.flavor = {"original_name": "m1.small"}
        server2 = object_fakes.make_server(uuid="s2")
        server2.flavor = {"original_name": "m1.large"}
        self.rp.preemptible_servers = [server1, server2]
        self.assertEqual([server1, server2], self.rp.preemptible_servers)
        self.assertIn("m1.small", self.rp.flavors_dict)
        self.assertIn("m1.large", self.rp.flavors_dict)

    def test_preemptible_resources(self):
        resources1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        resources2 = object_fakes.make_resources(vcpu=1, memory=256, disk=5)
        server1 = mock.Mock(resources=resources1)
        server2 = mock.Mock(resources=resources2)
        self.rp._preemptible_servers = [server1, server2]
        result = self.rp.preemptible_resources
        self.assertEqual(3, result.VCPU)

    def test_total_resources(self):
        total = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        caps = object_fakes.make_capabilities(total=total)
        self.rp._capabilities = caps
        result = self.rp.total_resources
        self.assertEqual(total, result)

    def test_used_resources(self):
        used = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        caps = object_fakes.make_capabilities(used=used)
        self.rp._capabilities = caps
        result = self.rp.used_resources
        self.assertEqual(used, result)

    def test_used_resources_setter(self):
        new_used = object_fakes.make_resources(vcpu=6, memory=1024, disk=30)
        self.rp.used_resources = new_used
        self.assertEqual(new_used, self.rp.used_resources)

    def test_free_resources(self):
        used = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        caps = object_fakes.make_capabilities(used=used, total=total)
        self.rp._capabilities = caps
        result = self.rp.free_resources
        self.assertIsNotNone(result)

    def test_eq(self):
        rp1 = object_fakes.make_resource_provider(uuid="same-uuid", name="rp1")
        rp2 = object_fakes.make_resource_provider(uuid="same-uuid", name="rp2")
        self.assertEqual(rp1, rp2)

    def test_hash(self):
        rp = object_fakes.make_resource_provider(uuid="rp-uuid", name="rp1")
        self.assertEqual(hash("rp-uuid"), hash(rp))

    def test_repr(self):
        rp = object_fakes.make_resource_provider(uuid="rp-uuid", name="rp1")
        r = repr(rp)
        self.assertIn("rp-uuid", r)
        self.assertIn("rp1", r)

    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_hypervisor(self, mock_hv_get):
        mock_hv = mock.Mock()
        mock_hv_get.return_value = mock_hv
        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        result = rp.hypervisor
        self.assertEqual(mock_hv, result)
        mock_hv_get.assert_called_once_with("rp-uuid")

    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_hypervisor_cached(self, mock_hv_get):
        mock_hv = mock.Mock()
        mock_hv_get.return_value = mock_hv
        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        _ = rp.hypervisor
        _ = rp.hypervisor
        # Should only call once (cached)
        mock_hv_get.assert_called_once()

    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_disabled_enabled(self, mock_hv_get, mock_service_status):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        result = rp.disabled
        self.assertFalse(result)

    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_disabled_forced_down(self, mock_hv_get, mock_service_status):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = True
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        result = rp.disabled
        self.assertTrue(result)

    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_disabled_state_down(self, mock_hv_get, mock_service_status):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "down"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        result = rp.disabled
        self.assertTrue(result)

    @mock.patch("aardvark.objects.resource_provider.instance.InstanceList")
    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_populate_projects(
        self, mock_hv_get, mock_service_status, mock_instance_list
    ):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        mock_server = mock.Mock()
        mock_server.flavor = {"original_name": "m1.small"}
        mock_instance_list.return_value.instances.return_value = [mock_server]

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        rp.populate_projects(["proj-uuid"])
        self.assertIn(mock_server, rp.preemptible_servers)

    @mock.patch("aardvark.objects.resource_provider.instance.InstanceList")
    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_populate_projects_already_populated(
        self, mock_hv_get, mock_service_status, mock_instance_list
    ):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        rp.populated = True
        rp.populate_projects(["proj-uuid"])
        mock_instance_list.return_value.instances.assert_not_called()

    @mock.patch("aardvark.objects.resource_provider.instance.InstanceList")
    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_populate_flavors(
        self, mock_hv_get, mock_service_status, mock_instance_list
    ):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        mock_server = mock.Mock()
        mock_server.flavor = {"original_name": "m1.small"}
        mock_instance_list.return_value.instances.return_value = [mock_server]

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        rp.populate_flavors(["flavor-id"])
        self.assertIn(mock_server, rp.preemptible_servers)

    @mock.patch("aardvark.objects.resource_provider.instance.InstanceList")
    @mock.patch("aardvark.api.nova.service_status")
    @mock.patch("aardvark.api.nova.hypervisor_get")
    def test_populate_sorted(
        self, mock_hv_get, mock_service_status, mock_instance_list
    ):
        mock_hv = mock.Mock()
        mock_hv.service = {"host": "host1"}
        mock_hv_get.return_value = mock_hv
        mock_service = mock.Mock()
        mock_service.forced_down = False
        mock_service.state = "up"
        mock_service.status = "enabled"
        mock_service_status.return_value = mock_service

        mock_server = mock.Mock()
        mock_server.flavor = {"original_name": "m1.small"}
        mock_instance_list.return_value.sorted_instances.return_value = [
            mock_server
        ]

        rp = resource_provider.ResourceProvider("rp-uuid", "rp1")
        rp.populate_sorted(["proj-uuid"])
        self.assertEqual([mock_server], rp.preemptible_servers)
        self.assertTrue(rp.populated)

    def test_populate(self):
        rp = object_fakes.make_resource_provider(uuid="rp-uuid", name="rp1")
        rp.populated = False
        with mock.patch.object(rp, "populate_projects") as mock_projects:
            with mock.patch.object(rp, "populate_flavors") as mock_flavors:
                rp.populate(["proj1"], ["flavor1"])
                mock_projects.assert_called_once_with(["proj1"])
                mock_flavors.assert_called_once_with(["flavor1"])
        self.assertTrue(rp.populated)


class ResourceProviderListTests(base.TestCase):
    @mock.patch("aardvark.api.placement.get_resource_providers")
    def test_resource_providers(self, mock_get_rps):
        rp1 = object_fakes.make_resource_provider(uuid="rp1", name="rp1_name")
        mock_get_rps.return_value = [rp1]
        rp_list = resource_provider.ResourceProviderList(aggregates=["agg1"])
        result = rp_list.resource_providers
        mock_get_rps.assert_called_once_with(["agg1"])
        self.assertEqual([rp1], result)
