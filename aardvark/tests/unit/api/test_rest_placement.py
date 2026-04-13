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

from keystoneauth1 import exceptions as keystone_exc

from aardvark.api.rest import placement
from aardvark.tests import base


class PlacementClientTests(base.TestCase):
    def setUp(self):
        super().setUp()
        self.client = placement.PlacementClient()

    def _mock_response(self, data):
        mock_resp = mock.Mock()
        mock_resp.json.return_value = data
        return mock_resp

    def test_resource_providers_no_aggregates(self):
        rps = [
            {"uuid": "rp1", "name": "rp1_name"},
            {"uuid": "rp2", "name": "rp2_name"},
        ]
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"resource_providers": rps}
        )
        result = self.client.resource_providers()
        self.assertEqual(2, len(result))
        call_args = self.client.client.get.call_args
        self.assertIn("/resource_providers", call_args[0][0])

    def test_resource_providers_with_aggregates(self):
        rps = [{"uuid": "rp1", "name": "rp1_name"}]
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"resource_providers": rps}
        )
        result = self.client.resource_providers(aggregates=["agg1", "agg2"])
        self.assertEqual(1, len(result))
        call_args = self.client.client.get.call_args
        self.assertIn("agg1", call_args[0][0])
        self.assertIn("agg2", call_args[0][0])

    def test_resource_providers_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.resource_providers()
        self.assertIsNone(result)

    def test_usages(self):
        usages = {"VCPU": 4, "MEMORY_MB": 1024}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"usages": usages}
        )
        result = self.client.usages("rp-uuid")
        self.assertEqual(usages, result)

    def test_usages_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.usages("rp-uuid")
        self.assertIsNone(result)

    def test_inventory(self):
        inv_data = {"total": 100, "reserved": 0, "allocation_ratio": 1.0}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(inv_data)
        result = self.client.inventory("rp-uuid", "VCPU")
        self.assertEqual(inv_data, result)

    def test_inventory_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.inventory("rp-uuid", "VCPU")
        self.assertIsNone(result)

    def test_inventories(self):
        inventories = {"VCPU": {"total": 100}, "MEMORY_MB": {"total": 2048}}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"inventories": inventories}
        )
        result = self.client.inventories("rp-uuid")
        self.assertEqual(inventories, result)

    def test_inventories_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.inventories("rp-uuid")
        self.assertIsNone(result)

    def test_resource_classes(self):
        classes = [{"name": "VCPU"}, {"name": "MEMORY_MB"}]
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"resource_classes": classes}
        )
        result = self.client.resource_classes()
        self.assertEqual(classes, result)

    def test_resource_classes_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.resource_classes()
        self.assertIsNone(result)

    def test_all_inventories(self):
        inv_data = {"some": "data"}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(inv_data)
        result = self.client.all_inventories()
        self.assertEqual(inv_data, result)

    def test_all_inventories_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.all_inventories()
        self.assertIsNone(result)

    def test_project_usages(self):
        usages = {"VCPU": 4}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"usages": usages}
        )
        result = self.client.project_usages("proj-uuid")
        self.assertEqual(usages, result)
        call_args = self.client.client.get.call_args
        self.assertIn("proj-uuid", call_args[0][0])

    def test_project_usages_with_user_id(self):
        usages = {"VCPU": 4}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"usages": usages}
        )
        result = self.client.project_usages("proj-uuid", user_id="user-uuid")
        self.assertEqual(usages, result)
        call_args = self.client.client.get.call_args
        self.assertIn("user_id=user-uuid", call_args[0][0])

    def test_project_usages_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.project_usages("proj-uuid")
        self.assertIsNone(result)

    def test_traits(self):
        traits = ["CUSTOM_TRAIT1", "HW_CPU_X86_SSE"]
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(
            {"traits": traits}
        )
        result = self.client.traits()
        self.assertEqual(traits, result)

    def test_traits_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.traits()
        self.assertIsNone(result)

    def test_get_allocations(self):
        alloc_data = {"allocations": {"rp-uuid": {"resources": {"VCPU": 2}}}}
        self.client.client = mock.Mock()
        self.client.client.get.return_value = self._mock_response(alloc_data)
        result = self.client.get_allocations("consumer-uuid")
        self.assertEqual(alloc_data, result)

    def test_get_allocations_not_found(self):
        self.client.client = mock.Mock()
        self.client.client.get.side_effect = keystone_exc.NotFound()
        result = self.client.get_allocations("consumer-uuid")
        self.assertIsNone(result)
