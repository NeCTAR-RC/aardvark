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


from aardvark.objects import capabilities
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes


class CapabilitiesTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def test_capabilities(self):
        used = fakes.make_resources(vcpu=1, memory=2000, disk=20)
        total = fakes.make_resources(vcpu=8, memory=8000, disk=80)
        capab = capabilities.Capabilities(used, total)

        free = fakes.make_resources(vcpu=7, memory=6000, disk=60)
        self.assertEqual(free, capab.free_resources)
        self.assertEqual(25, capab.usage())

        used = fakes.make_resources(vcpu=8, memory=8000, disk=80)
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab = capabilities.Capabilities(used, total)

        free = fakes.make_resources(vcpu=2, memory=2000, disk=20)
        self.assertEqual(free, capab.free_resources)
        self.assertEqual(80, capab.usage())

        used = fakes.make_resources(memory=4000, disk=60)
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab = capabilities.Capabilities(used, total)

        free = fakes.make_resources(vcpu=10, memory=6000, disk=40)
        self.assertEqual(free, capab.free_resources)
        self.assertEqual(60, capab.usage())

    def test_excessive_resources(self):
        used = fakes.make_resources(vcpu=8, memory=8000, disk=80)
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab = capabilities.Capabilities(used, total)

        excessive = fakes.make_resources(vcpu=1, memory=1000, disk=10)
        self.assertEqual(excessive, capab.get_excessive_resources(70))

        excessive = fakes.make_resources(vcpu=1, memory=500, disk=5)
        self.assertEqual(excessive, capab.get_excessive_resources(75))

        excessive = fakes.make_resources()
        self.assertEqual(excessive, capab.get_excessive_resources(90))

        used = fakes.make_resources(vcpu=3, memory=6000, disk=80)
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab = capabilities.Capabilities(used, total)

        excessive = fakes.make_resources(memory=1000, disk=30)
        self.assertEqual(excessive, capab.get_excessive_resources(50))

        excessive = fakes.make_resources(disk=20)
        self.assertEqual(excessive, capab.get_excessive_resources(60))

    def test_addition(self):
        used = fakes.make_resources(vcpu=8, memory=8000, disk=80)
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab1 = capabilities.Capabilities(used, total)

        self.assertEqual(80, capab1.usage())

        used = fakes.make_resources()
        total = fakes.make_resources(vcpu=10, memory=10000, disk=100)
        capab2 = capabilities.Capabilities(used, total)

        self.assertEqual(0, capab2.usage())

        capab3 = capab1 + capab2
        free = fakes.make_resources(vcpu=12, memory=12000, disk=120)
        self.assertEqual(40, capab3.usage())
        self.assertEqual(free, capab3.free_resources)
