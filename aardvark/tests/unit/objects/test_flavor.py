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


from aardvark.objects import flavor
from aardvark.tests import base


class FlavorTests(base.TestCase):
    def test_flavor_init(self):
        f = flavor.Flavor("flavor-id", "m1.small", preemptible=True)
        self.assertEqual("flavor-id", f.id)
        self.assertEqual("m1.small", f.name)
        self.assertTrue(f.preemptible)

    def test_flavor_default_preemptible(self):
        f = flavor.Flavor("flavor-id", "m1.small")
        self.assertFalse(f.preemptible)


class FlavorListTests(base.TestCase):
    @mock.patch("aardvark.api.nova.get_preemptible_flavors")
    @mock.patch("oslo_cache.configure_cache_region")
    @mock.patch("oslo_cache.create_region")
    def test_preemptible_flavors(
        self, mock_create_region, mock_configure, mock_get_flavors
    ):
        mock_flavor = mock.Mock()
        mock_flavor.id = "flavor-id"
        mock_flavor.name = "preemptible.small"
        mock_get_flavors.return_value = [mock_flavor]
        mock_cache = mock.Mock()
        mock_cache.get.return_value = None
        mock_configure.return_value = mock_cache

        fl = flavor.FlavorList()
        result = fl.preemptible_flavors
        self.assertEqual(1, len(result))
        self.assertEqual("flavor-id", result[0].id)
        self.assertTrue(result[0].preemptible)

    @mock.patch("aardvark.api.nova.get_preemptible_flavors")
    @mock.patch("oslo_cache.configure_cache_region")
    @mock.patch("oslo_cache.create_region")
    def test_preemptible_flavors_cached(
        self, mock_create_region, mock_configure, mock_get_flavors
    ):
        mock_flavor = mock.Mock()
        mock_flavor.id = "flavor-id"
        mock_flavor.name = "preemptible.small"
        mock_get_flavors.return_value = [mock_flavor]

        # Simulate cache hit on second call
        cached_flavors = [
            flavor.Flavor("flavor-id", "preemptible.small", True)
        ]
        mock_cache = mock.Mock()
        mock_cache.get.return_value = cached_flavors
        mock_configure.return_value = mock_cache

        fl = flavor.FlavorList()
        result = fl.preemptible_flavors
        self.assertEqual(cached_flavors, result)
        # nova should not be called since cache returned data
        mock_get_flavors.assert_not_called()

    @mock.patch("aardvark.api.nova.get_preemptible_flavors")
    @mock.patch("oslo_cache.configure_cache_region")
    @mock.patch("oslo_cache.create_region")
    def test_preemptible_flavors_empty(
        self, mock_create_region, mock_configure, mock_get_flavors
    ):
        mock_get_flavors.return_value = []
        mock_cache = mock.Mock()
        mock_cache.get.return_value = None
        mock_configure.return_value = mock_cache

        fl = flavor.FlavorList()
        result = fl.preemptible_flavors
        self.assertEqual([], result)
