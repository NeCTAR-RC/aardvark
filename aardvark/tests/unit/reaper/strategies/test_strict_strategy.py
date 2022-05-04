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
from aardvark import exception
from aardvark.reaper.strategies import strict
from aardvark.reaper.strategies import utils
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


class StrictStrategyTests(base.TestCase):

    def setUp(self):
        super(StrictStrategyTests, self).setUp()
        self.strategy = strict.StrictStrategy(watermark_mode=False)

    def test_find_matching_server_combinations_one_server(self):
        used = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        servers = [server1]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=5)
        result = self.strategy.find_matching_server_combinations(
            [host], requested, None)
        expected_instances = [server1]
        exepected_leftovers = object_fakes.make_resources(disk=5)
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host.uuid, result.provider.uuid)

    def test_find_matching_server_combinations(self):
        used = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1', flavor_name='flavor1')
        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid='server2', flavor_name='flavor2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid='server3', flavor_name='flavor3')
        servers = [server1, server2, server3]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=5)
        result = self.strategy.find_matching_server_combinations(
            [host], requested, None)
        expected_instances = [server2]
        exepected_leftovers = object_fakes.make_resources()
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host.uuid, result.provider.uuid)

    def test_find_matching_server_combinations_multiple_hosts(self):
        used1 = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        servers1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), uuid='server1'),
        ]

        host1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        host1.preemptible_servers = servers1

        used2 = object_fakes.make_resources(vcpu=7, memory=1500, disk=35)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers2 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), uuid='server2'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), uuid='server3')
        ]

        host2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)

        host2.preemptible_servers = servers2
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        result = self.strategy.find_matching_server_combinations(
            [host1, host2], requested, None)
        expected_instances = servers1
        exepected_leftovers = object_fakes.make_resources()
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host1.uuid, result.provider.uuid)

    def test_find_matching_server_combinations_enough_free(self):
        used = object_fakes.make_resources(vcpu=7, memory=512, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid='server2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid='server3')
        servers = [server1, server2, server3]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=5)
        result = self.strategy.find_matching_server_combinations(
            [host], requested, None)
        expected_instances = []
        exepected_leftovers = object_fakes.make_resources(memory=1288)
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host.uuid, result.provider.uuid)

    def test_find_matching_server_combinations_enough_free_mult_hosts(self):
        used1 = object_fakes.make_resources(vcpu=7, memory=256, disk=35)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        servers1 = [server1]

        host1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        host1.preemptible_servers = servers1

        used2 = object_fakes.make_resources(vcpu=7, memory=512, disk=35)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid='server2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid='server3')
        servers2 = [server2, server3]

        host2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)

        host2.preemptible_servers = servers2
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=5)
        result = self.strategy.find_matching_server_combinations(
            [host1, host2], requested, None)
        expected_instances = []
        exepected_leftovers = object_fakes.make_resources(memory=1288)
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host2.uuid, result.provider.uuid)

    def test_find_matching_server_combinations_not_enough(self):
        used = object_fakes.make_resources(vcpu=7, memory=512, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid='server2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid='server3')
        servers = [server1, server2, server3]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=35)
        result = self.strategy.find_matching_server_combinations(
            [host], requested, None)
        self.assertIsNone(result)

    def test_find_matching_server_combinations_not_enough_multiple_hosts(self):
        used1 = object_fakes.make_resources(vcpu=7, memory=256, disk=35)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        servers1 = [server1]

        host1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        host1.preemptible_servers = servers1

        used2 = object_fakes.make_resources(vcpu=7, memory=512, disk=35)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=5),
            uuid='server2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=10),
            uuid='server3')
        servers2 = [server2, server3]

        host2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)

        host2.preemptible_servers = servers2
        requested = object_fakes.make_resources(vcpu=1, memory=256, disk=35)
        result = self.strategy.find_matching_server_combinations(
            [host1, host2], requested, None)
        self.assertIsNone(result)

    def test_find_matching_server_combinations_mixed_resources(self):
        used = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=2, memory=512, disk=5),
            uuid='server1', flavor_name='flavor1')
        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server2', flavor_name='flavor2')
        servers = [server1, server2]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        CONF.reaper.vcpu_sorting_priority = 2
        CONF.reaper.ram_sorting_priority = 1
        CONF.reaper.disk_sorting_priority = 3
        result = self.strategy.find_matching_server_combinations(
            [host], requested, None)
        expected_instances = [server2]
        exepected_leftovers = object_fakes.make_resources(disk=5)
        self.assertEqual(expected_instances, result.instances)
        self.assertEqual(exepected_leftovers, result.leftovers)
        self.assertEqual(host.uuid, result.provider.uuid)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers_no_combinations(self, mocked_find):
        mocked_find.return_value = None
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        self.assertRaises(exception.NotEnoughResources,
                          self.strategy.get_preemptible_servers,
                          requested, fake_hosts, 1, fake_projects)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers(self, mocked_find):
        used = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        server = mock.Mock(resources=object_fakes.make_resources(
            vcpu=1, memory=256, disk=10), uuid='server1')
        combo = utils.Combination(provider=host, instances=[server],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10))
        mocked_find.return_value = combo
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, fake_hosts, 1, fake_projects)
        self.assertEqual([host], sel_hosts)
        self.assertEqual([server], sel_servers)

    def test_get_preemptible_servers_enough_free(self):
        used = object_fakes.make_resources(vcpu=6, memory=1200, disk=30)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, [host], 1, fake_projects)
        self.assertEqual([host], sel_hosts)
        self.assertEqual([], sel_servers)

    def test_get_preemptible_servers_enough_free_multiple_spots(self):
        used = object_fakes.make_resources(vcpu=4, memory=1000, disk=20)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, [host], 2, fake_projects)
        self.assertEqual([host], sel_hosts)
        self.assertEqual([], sel_servers)


class StrictStrategyWatermarkModeTests(base.TestCase):

    def setUp(self):
        super(StrictStrategyWatermarkModeTests, self).setUp()
        self.strategy = strict.StrictStrategy(watermark_mode=True)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers(self, mocked_find):
        used = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        server = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        combo = utils.Combination(provider=host, instances=[server],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10))
        mocked_find.return_value = combo
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, fake_hosts, 1, fake_projects)
        self.assertEqual([host], sel_hosts)
        self.assertEqual([server], sel_servers)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers_no_combinations(self, mocked_find):
        mocked_find.return_value = None
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        # Make sure that in watermark mode even if we don't have enough
        # resources, no exception is raised.
        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, fake_hosts, 1, fake_projects)
        self.assertEqual([], sel_hosts)
        self.assertEqual([], sel_servers)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers_not_enough(self, mocked_find):
        used = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        server = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        combo = utils.Combination(provider=host, instances=[server],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10))
        mocked_find.side_effect = [combo, None]
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        # Make sure that in watermark mode even if we don't have enough
        # resources, no exception is raised.
        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, fake_hosts, 2, fake_projects)
        self.assertEqual([host], sel_hosts)
        self.assertEqual([server], sel_servers)

    @mock.patch('aardvark.reaper.strategies.strict.StrictStrategy.'
                'find_matching_server_combinations')
    def test_get_preemptible_servers_multiple_hosts(self, mocked_find):
        used = object_fakes.make_resources(vcpu=7, memory=1800, disk=35)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)
        host1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp_capabilities)
        server1 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server1')
        server2 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server2')
        server3 = object_fakes.make_server(
            resources=object_fakes.make_resources(vcpu=1, memory=256, disk=10),
            uuid='server3')
        combo1 = utils.Combination(provider=host1, instances=[server1],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10))
        combo2 = utils.Combination(
            provider=host2, instances=[server2, server3],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10))
        mocked_find.side_effect = [combo1, combo2, None]
        fake_hosts = [mock.Mock()]
        fake_projects = [mock.Mock()]
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        # Make sure that in watermark mode even if we don't have enough
        # resources, no exception is raised.
        sel_hosts, sel_servers = self.strategy.get_preemptible_servers(
            requested, fake_hosts, 2, fake_projects)
        self.assertEqual([host1, host2], sel_hosts)
        self.assertEqual([server1, server2, server3], sel_servers)
