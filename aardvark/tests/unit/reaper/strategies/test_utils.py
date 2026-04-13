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


import aardvark.conf
from aardvark.reaper.strategies import utils
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


class StrategyUtilsTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def test_sort_combinations(self):
        combo1 = utils.Combination(
            provider="host1",
            instances=["server1"],
            leftovers=object_fakes.make_resources(vcpu=2, memory=256, disk=10),
        )

        combo2 = utils.Combination(
            provider="host2",
            instances=["server2"],
            leftovers=object_fakes.make_resources(vcpu=1, memory=512, disk=10),
        )

        combo3 = utils.Combination(
            provider="host3",
            instances=["server3"],
            leftovers=object_fakes.make_resources(vcpu=1, memory=512, disk=20),
        )

        combinations = [combo1, combo2, combo3]

        CONF.reaper.vcpu_sorting_priority = 2
        CONF.reaper.ram_sorting_priority = 1
        CONF.reaper.disk_sorting_priority = 3
        result = utils.sort_combinations(combinations)
        self.assertEqual(combo1, result)

        CONF.reaper.vcpu_sorting_priority = 1
        CONF.reaper.ram_sorting_priority = 2
        CONF.reaper.disk_sorting_priority = 3
        result = utils.sort_combinations(combinations)
        self.assertEqual(combo2, result)

        CONF.reaper.vcpu_sorting_priority = 2
        CONF.reaper.ram_sorting_priority = 3
        CONF.reaper.disk_sorting_priority = 1
        result = utils.sort_combinations(combinations)
        self.assertEqual(combo2, result)
