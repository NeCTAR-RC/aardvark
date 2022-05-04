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
from aardvark.reaper.strategies import chance
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


def mocked_random(arg):
    return arg


class ChanceStrategyTests(base.TestCase):

    def setUp(self):
        super(ChanceStrategyTests, self).setUp()
        CONF.reaper.alternatives = 1
        CONF.reaper.max_attempts = 10
        self.strategy = chance.ChanceStrategy(watermark_mode=False)

    @mock.patch('aardvark.reaper.strategies.chance.ChanceStrategy.'
                'select_servers')
    @mock.patch('aardvark.reaper.strategy.ReaperStrategy.check_spots')
    def test_get_preemptible_servers(self, spots, select):
        selected_servers = ['server1']
        pre1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        free1 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        selected_hosts = [
            mock.Mock(free_resources=free1, preemptible_resources=pre1,
                      disabled=False)
        ]
        select.return_value = selected_servers

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        projects = [mock.Mock()]
        self.assertEqual((selected_hosts, selected_servers),
            self.strategy.get_preemptible_servers(requested, selected_hosts, 1,
                                                  projects))
        spots.assert_called_once_with(selected_hosts, 1)

    def test_select_servers_enough_free(self):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=25)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=50)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        self.assertEqual([], self.strategy.select_servers(host, requested))
        res = object_fakes.make_resources(vcpu=4, memory=1024, disk=25)
        expected_used = res + requested
        self.assertEqual(expected_used, host.used_resources)
        self.assertEqual(1, host.reserved_spots)

    def test_select_servers_not_enough_resources(self):
        used = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        servers = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), uuid='server2'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), uuid='server3')
        ]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=6, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual([], self.strategy.select_servers(host, requested))
            self.assertEqual(0, host.reserved_spots)
            self.assertEqual(3, len(host.preemptible_servers))

    def test_select_servers_out_of_retries(self):
        CONF.reaper.max_attempts = 2

        used = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp_capabilities = object_fakes.make_capabilities(
           used=used, total=total)

        servers = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), uuid='server2'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), uuid='server3')
        ]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp_capabilities)
        host.preemptible_servers = servers

        requested = object_fakes.make_resources(vcpu=6, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual([], self.strategy.select_servers(host, requested))
            self.assertEqual(0, host.reserved_spots)
            self.assertEqual(3, len(host.preemptible_servers))

    def test_multiple_spots_one_host(self):
        used1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        total1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=4, memory=1024, disk=20), uuid='server1'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp1.populate = mock.Mock()

        rps = [rp1]

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        projects = [mock.Mock()]

        expected = (rps, servers_rp1)
        exp_used = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)

        actual = self.strategy.get_preemptible_servers(requested,
                                                       rps, 2,
                                                       projects)
        self.assertEqual(expected, actual)
        self.assertEqual(exp_used, rp1.used_resources)
        self.assertEqual(2, rp1.reserved_spots)
        self.assertEqual(0, len(rp1.preemptible_servers))

    def test_multiple_spots_one_host_enough_free(self):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.populate = mock.Mock()

        rps = [rp1]

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        projects = [mock.Mock()]

        expected = (rps, [])
        exp_used = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)

        actual = self.strategy.get_preemptible_servers(requested,
                                                       rps, 2,
                                                       projects)
        self.assertEqual(expected, actual)
        self.assertEqual(exp_used, rp1.used_resources)
        self.assertEqual(2, rp1.reserved_spots)

    def test_multiple_spots_multiple_hosts(self):
        used1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        total1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=4, memory=1792, disk=20)
        total2 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server2'),
        ]

        servers_rp2 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), uuid='server3'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server4'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp1.populate = mock.Mock()
        rp2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)
        rp2.preemptible_servers = servers_rp2
        rp2.populate = mock.Mock()

        rps = [rp1, rp2]

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        projects = [mock.Mock()]

        expected = (rps, servers_rp1 + [servers_rp2[0]])

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            with mock.patch('random.choice') as mocked_choice:
                mocked_choice.side_effect = rps
                actual = self.strategy.get_preemptible_servers(requested,
                                                               rps, 2,
                                                               projects)
                self.assertEqual(expected, actual)
                self.assertEqual(1, rp1.reserved_spots)
                self.assertEqual(1, rp2.reserved_spots)
                self.assertEqual(0, len(rp1.preemptible_servers))
                self.assertEqual(1, len(rp2.preemptible_servers))
                self.assertEqual('server4', rp2.preemptible_servers[0].uuid)

    def test_not_enough_resources(self):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server2'),
        ]

        servers_rp2 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server3'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server4'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp1.populate = mock.Mock()
        rp2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)
        rp2.preemptible_servers = servers_rp2
        rp2.populate = mock.Mock()

        rps = [rp1, rp2]

        requested = object_fakes.make_resources(disk=50)
        projects = [mock.Mock()]

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            with mock.patch('random.choice') as mocked_choice:
                mocked_choice.side_effect = rps
                self.assertRaises(exception.NotEnoughResources,
                                  self.strategy.get_preemptible_servers,
                                  requested, rps, 1, projects)


class ChanceStrategyWatermarkModeTests(base.TestCase):

    def setUp(self):
        super(ChanceStrategyWatermarkModeTests, self).setUp()
        CONF.reaper.max_attempts = 10
        self.strategy = chance.ChanceStrategy(watermark_mode=True)

    @mock.patch('aardvark.reaper.strategies.chance.ChanceStrategy.'
                'select_servers')
    @mock.patch('aardvark.reaper.strategy.ReaperStrategy.check_spots')
    def test_get_preemptible_servers(self, spots, select):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server2'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)

        requested = object_fakes.make_resources(disk=10)
        hosts = [rp1, rp2]

        projects = [mock.Mock()]
        select.return_value = [servers_rp1[0]]
        with mock.patch('random.choice') as mocked:
            mocked.return_value = hosts[0]

            expected = ([hosts[0]], [servers_rp1[0]])
            result = self.strategy.get_preemptible_servers(
                requested, hosts, 1, projects)

            self.assertEqual(expected, result)
        spots.assert_not_called()

    def test_select_servers_not_enough(self):
        # In the watermark mode even if the host preemptible resources
        # are not enough, we will try to free those resources.
        used1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=50)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=50)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        servers = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=512, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=512, disk=10), uuid='server2'),
        ]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        host.preemptible_servers = servers
        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=40)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            result = self.strategy.select_servers(host, requested)
            self.assertEqual(servers, result)
            self.assertEqual(0, len(host.preemptible_servers))

    def test_select_servers(self):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=25)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=50)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        servers = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=5), uuid='server2'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=512, disk=10), uuid='server3')
        ]

        host = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        host.preemptible_servers = servers

        requested = object_fakes.make_resources(vcpu=2, memory=512, disk=10)

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            self.assertEqual([servers[0], servers[1]],
                             self.strategy.select_servers(host, requested))
            self.assertEqual(1, len(host.preemptible_servers))
            self.assertEqual('server3', host.preemptible_servers[0].uuid)
            self.assertEqual(1, host.reserved_spots)

    @mock.patch('aardvark.reaper.strategy.ReaperStrategy.check_spots')
    def test_full_execution(self, spots):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server2'),
        ]

        servers_rp2 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server3'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=256, disk=10), uuid='server4'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)
        rp2.preemptible_servers = servers_rp2

        rps = [rp1, rp2]

        expected_result = (rps[:], servers_rp1[:] + servers_rp2[:])

        requested = object_fakes.make_resources(disk=50)
        projects = [mock.Mock()]

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            with mock.patch('random.choice') as mocked_choice:
                mocked_choice.side_effect = rps
                result = self.strategy.get_preemptible_servers(
                    requested, rps, 1, projects)

                self.assertEqual(expected_result, result)

                self.assertEqual(0, len(rp1.preemptible_servers))
                self.assertEqual(0, len(rp2.preemptible_servers))

    @mock.patch('aardvark.reaper.strategy.ReaperStrategy.check_spots')
    def test_big_request_for_resources(self, spots):
        used1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total1 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp1_capabilities = object_fakes.make_capabilities(
           used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        total2 = object_fakes.make_resources(vcpu=8, memory=2056, disk=40)
        rp2_capabilities = object_fakes.make_capabilities(
           used=used2, total=total2)

        servers_rp1 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server1'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server2'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server3'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server4')
        ]

        servers_rp2 = [
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=128, disk=5), uuid='server5'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=128, disk=5), uuid='server6'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=128, disk=5), uuid='server7'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=1, memory=128, disk=5), uuid='server8'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server9'),
            object_fakes.make_server(
                resources=object_fakes.make_resources(
                vcpu=2, memory=256, disk=10), uuid='server10'),
        ]

        rp1 = object_fakes.make_resource_provider(
            uuid='1', name='rp1', capabilities=rp1_capabilities)
        rp1.preemptible_servers = servers_rp1
        rp2 = object_fakes.make_resource_provider(
            uuid='2', name='rp2', capabilities=rp2_capabilities)
        rp2.preemptible_servers = servers_rp2

        rps = [rp1, rp2]

        expected = (rps[:], servers_rp1[:] + servers_rp2[:])

        requested = object_fakes.make_resources(disk=80)
        projects = [mock.Mock()]

        with mock.patch('random.shuffle') as mocked:
            mocked.side_effect = mocked_random
            with mock.patch('random.choice') as mocked_choice:
                mocked_choice.side_effect = rps
                result = self.strategy.get_preemptible_servers(
                    requested, rps, 1, projects)
                self.assertEqual(expected, result)
                self.assertEqual(0, len(rp1.preemptible_servers))
                self.assertEqual(0, len(rp2.preemptible_servers))
