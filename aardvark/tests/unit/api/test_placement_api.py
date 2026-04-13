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

from aardvark.api import placement
from aardvark.tests import base


class PlacementAPITests(base.TestCase):
    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_resource_providers(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.resource_providers.return_value = [
            {"uuid": "rp1", "name": "rp1_name"},
            {"uuid": "rp2", "name": "rp2_name"},
        ]
        result = placement.get_resource_providers()
        self.assertEqual(2, len(result))
        self.assertEqual("rp1", result[0].uuid)
        self.assertEqual("rp1_name", result[0].name)

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_resource_providers_with_aggregates(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.resource_providers.return_value = [
            {"uuid": "rp1", "name": "rp1_name"},
        ]
        result = placement.get_resource_providers(aggregates=["agg1"])
        mock_client.resource_providers.assert_called_once_with(["agg1"])
        self.assertEqual(1, len(result))

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_resource_provider_usages(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.usages.return_value = {"VCPU": 4, "MEMORY_MB": 1024}
        result = placement.get_resource_provider_usages("rp-uuid")
        mock_client.usages.assert_called_once_with("rp-uuid")
        self.assertEqual(4, result.VCPU)

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_resource_provider_inventories(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.inventories.return_value = {
            "VCPU": {
                "total": 100,
                "reserved": 0,
                "allocation_ratio": 1.0,
                "used": 50,
            }
        }
        result = placement.get_resource_provider_inventories("rp-uuid")
        mock_client.inventories.assert_called_once_with("rp-uuid")
        self.assertIsNotNone(result)

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_consumer_allocations(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_allocations.return_value = {
            "allocations": {
                "rp-uuid": {"resources": {"VCPU": 2, "MEMORY_MB": 512}}
            }
        }
        result = placement.get_consumer_allocations("consumer-uuid", "rp-uuid")
        self.assertEqual(2, result.VCPU)

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_consumer_allocations_no_rp(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.get_allocations.return_value = {"allocations": {}}
        result = placement.get_consumer_allocations("consumer-uuid", "rp-uuid")
        # Should return empty resources when rp not in allocations
        self.assertEqual(0, result.VCPU if hasattr(result, "VCPU") else 0)

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_resource_classes(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.resource_classes.return_value = [
            {"name": "VCPU"},
            {"name": "MEMORY_MB"},
        ]
        result = placement.get_resource_classes()
        self.assertEqual(2, len(result))

    @mock.patch("aardvark.api.placement._get_placement_client")
    def test_get_traits(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.traits.return_value = ["CUSTOM_TRAIT1"]
        result = placement.get_traits()
        self.assertEqual(["CUSTOM_TRAIT1"], result)
