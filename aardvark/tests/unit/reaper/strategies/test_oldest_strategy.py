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

import aardvark.conf
from aardvark.reaper.strategies import oldest
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


class OldestStrategyTests(base.TestCase):
    def setUp(self):
        super().setUp()
        CONF.reaper.parallel_timeout = 10
        self.strategy = oldest.OldestStrategy(watermark_mode=False)

    def test_get_preemptible_servers_enough_resources(self):
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=5)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid="server1",
        )
        server1.created = "2019-01-01T00:00:00Z"

        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host.preemptible_servers = [server1]
        host.populate = mock.Mock()

        projects = [mock.Mock()]
        result = self.strategy.get_preemptible_servers(
            requested, [host], 1, projects
        )
        selected_hosts, selected_servers = result
        self.assertEqual([], selected_hosts)
        self.assertIn(server1, selected_servers)

    def test_get_preemptible_servers_no_servers(self):
        requested = object_fakes.make_resources(vcpu=10, memory=2048, disk=50)

        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host.preemptible_servers = []
        host.populate = mock.Mock()

        projects = [mock.Mock()]
        result = self.strategy.get_preemptible_servers(
            requested, [host], 1, projects
        )
        selected_hosts, selected_servers = result
        self.assertEqual([], selected_hosts)
        self.assertEqual([], selected_servers)

    def test_get_preemptible_servers_multiple_servers_sorted_by_age(self):
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid="server1",
        )
        server1.created = "2019-01-01T00:00:00Z"

        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid="server2",
        )
        server2.created = "2019-06-01T00:00:00Z"

        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host.preemptible_servers = [server2, server1]
        host.populate = mock.Mock()

        projects = [mock.Mock()]
        result = self.strategy.get_preemptible_servers(
            requested, [host], 1, projects
        )
        selected_hosts, selected_servers = result
        # Oldest first (server1 is older)
        self.assertIn(server1, selected_servers)

    def test_find_matching_instances_disabled_host(self):
        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host._disabled = True
        host.populate = mock.Mock()

        result = self.strategy.find_matching_instances([host], [], [])
        self.assertEqual([], result)

    def test_find_matching_instances_enabled_host(self):
        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid="server1",
        )

        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host.preemptible_servers = [server1]
        host.populate = mock.Mock()

        result = self.strategy.find_matching_instances([host], [], [])
        self.assertIn(server1, result)

    def test_populate_host(self):
        host = mock.Mock()
        projects = ["proj1"]
        flavors = ["flavor1"]
        self.strategy.populate_host(host, projects, flavors)
        host.populate.assert_called_once_with(projects, flavors)

    def test_filter_servers(self):
        server1 = object_fakes.make_server(uuid="server1")
        host = object_fakes.make_resource_provider(uuid="1", name="rp1")
        host.preemptible_servers = [server1]
        result = self.strategy.filter_servers(host)
        self.assertEqual([server1], result)
