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
from aardvark import exception
from aardvark.reaper.strategies import chance
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


CONF = aardvark.conf.CONF


class ReaperStrategyTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def test_check_spots(self):
        strategy = chance.ChanceStrategy(False)
        hosts = [object_fakes.make_resource_provider(reserved_spots=1)]
        # No exception is raised
        strategy.check_spots(hosts, 1)

        # Asking for two slots should raise it
        self.assertRaises(
            exception.NotEnoughResources, strategy.check_spots, hosts, 2
        )

    def test_check_spots_multiple_hosts(self):
        strategy = chance.ChanceStrategy(False)
        hosts = [
            object_fakes.make_resource_provider(reserved_spots=1),
            object_fakes.make_resource_provider(reserved_spots=1),
        ]
        # No exception is raised
        strategy.check_spots(hosts, 2)

        # Asking for more spots should raise the exception
        self.assertRaises(
            exception.NotEnoughResources, strategy.check_spots, hosts, 3
        )
