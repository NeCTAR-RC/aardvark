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


from aardvark.objects import resources
from aardvark.tests import base
from aardvark.tests.unit.notifications import fakes as notification_fakes
from aardvark.tests.unit.objects import fakes


class ResourcesTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def test_resources_from_flavor_payload(self):
        payload = notification_fakes.make_flavor_payload(
            "uuid", vcpus=1, ephemeral=20, root_gb=30, swap=10, ram=30000
        )
        res = resources.Resources.obj_from_payload(payload["nova_object.data"])
        expected = fakes.make_resources(vcpu=1, memory=30000, disk=60)
        self.assertEqual(expected, res)

    def test_resources_from_flavor_payload_bfv(self):
        payload = notification_fakes.make_flavor_payload(
            "uuid", vcpus=1, ephemeral=20, root_gb=30, swap=10, ram=30000
        )
        res = resources.Resources.obj_from_payload(
            payload["nova_object.data"], is_bfv=True
        )
        expected = fakes.make_resources(vcpu=1, memory=30000)
        self.assertEqual(expected, res)

    def test_resources_from_flavor(self):
        flavor = fakes.make_flavor(
            "uuid", vcpus=1, ephemeral=20, root_gb=30, swap=10, ram=30000
        )
        res = resources.Resources.obj_from_flavor(flavor)
        expected = fakes.make_resources(vcpu=1, memory=30000, disk=60)
        self.assertEqual(expected, res)

    def test_resources_from_inventories(self):
        inventories = {
            "VCPU": fakes.make_inventory_dict(ratio=16, total=8),
            "DISK_GB": fakes.make_inventory_dict(reserved=5, total=80),
            "MEMORY_MB": fakes.make_inventory_dict(reserved=200, total=1200),
        }
        res = resources.Resources.obj_from_inventories(inventories)
        expected = fakes.make_resources(vcpu=128, disk=75, memory=1000)
        self.assertEqual(expected, res)

    def test_resources_comparisons(self):
        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        res2 = fakes.make_resources(vcpu=1, memory=512, disk=10)

        self.assertTrue(res1 >= res2)
        self.assertTrue(res1 != res2)
        # TODO(ttsiouts): check this
        self.assertFalse(res1 > res2)
        self.assertFalse(res1 <= res2)
        self.assertFalse(res1 == res2)

    def test_resources_sum_same_rcs(self):
        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        res2 = fakes.make_resources(vcpu=1, memory=512, disk=10)
        expected = fakes.make_resources(vcpu=2, memory=1024, disk=30)
        self.assertTrue(res1 + res2 == expected)

        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        res2 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        expected = fakes.make_resources(vcpu=2, memory=1024, disk=40)
        self.assertTrue(res1 + res2 == expected)

    def test_resources_sum_not_same_rcs(self):
        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        res2 = fakes.make_resources(vcpu=1, memory=512)
        expected = fakes.make_resources(vcpu=2, memory=1024, disk=20)
        self.assertTrue(res1 + res2 == expected)

    def test_resources_sub_not_same_rcs(self):
        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        res2 = fakes.make_resources(vcpu=1, memory=512, disk=10)
        expected = fakes.make_resources(disk=10)
        self.assertTrue(res1 - res2 == expected)

    def test_resources_mult(self):
        mult = 3
        res1 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        expected = fakes.make_resources(vcpu=3, memory=1536, disk=60)
        self.assertTrue(res1 * mult == expected)

    def test_resources_div(self):
        # Need to revisit this
        # res1 = fakes.make_resources(vcpu=3, memory=1536, disk=60)
        # res2 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        # expected = 3
        # self.assertTrue(res1 / res2 == expected)
        pass

    def test_resources_div_least(self):
        # Need to revisit this
        # res1 = fakes.make_resources(vcpu=100, memory=5120, disk=40)
        # res2 = fakes.make_resources(vcpu=1, memory=512, disk=20)
        # expected = 2
        # self.assertTrue(res1 / res2 == expected)
        pass

    def test_comparisons(self):
        res1 = fakes.make_resources(vcpu=1, memory=512)
        res2 = fakes.make_resources(memory=512)
        self.assertTrue(res1 >= res2)
        self.assertTrue(not res1 <= res2)
        self.assertTrue(not res1 < res2)

        res1 = fakes.make_resources(memory=512)
        res2 = fakes.make_resources(vcpu=1, memory=512)
        self.assertTrue(res1 <= res2)
        self.assertTrue(res1 >= res2)
        self.assertTrue(not res1 < res2)

        res1 = fakes.make_resources()
        res2 = fakes.make_resources()
        self.assertTrue(res1 >= res2)
        self.assertTrue(res1 <= res2)
        self.assertTrue(res1 == res2)
