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
from aardvark.objects import inventory
from aardvark.tests import base


CONF = aardvark.conf.CONF


def make_inventory(
    resource_class="VCPU",
    total=100,
    used=50,
    allocation_ratio=1.0,
    reserved=0,
    **kwargs,
):
    kw = {
        "allocation_ratio": allocation_ratio,
        "reserved": reserved,
        "total": total,
        "used": used,
    }
    kw.update(kwargs)
    return inventory.Inventory(resource_class, **kw)


class InventoryTests(base.TestCase):
    def setUp(self):
        super().setUp()
        CONF.aardvark.watermark = 80

    def test_init_basic(self):
        inv = make_inventory(total=100, used=50)
        self.assertEqual(50.0, inv.used)
        self.assertEqual(100.0, inv.total)

    def test_init_with_reservation(self):
        inv = make_inventory(total=100, used=50, reserved=10)
        # total = (100 - 10) * 1.0 = 90
        self.assertEqual(90.0, inv.total)

    def test_init_with_allocation_ratio(self):
        inv = make_inventory(
            total=100, used=50, allocation_ratio=2.0, reserved=0
        )
        # total = (100 - 0) * 2.0 = 200
        self.assertEqual(200.0, inv.total)

    def test_init_missing_optional_attrs(self):
        # If optional attrs like max_unit, step_size, min_unit are missing,
        # they should default to 0.0
        inv = make_inventory()
        self.assertEqual(0.0, inv.max_unit)
        self.assertEqual(0.0, inv.step_size)
        self.assertEqual(0.0, inv.min_unit)

    def test_free(self):
        inv = make_inventory(total=100, used=60)
        self.assertEqual(40.0, inv.free)

    def test_usage(self):
        inv = make_inventory(total=100, used=50)
        self.assertEqual(50.0, inv.usage)

    def test_usage_zero_total(self):
        inv = make_inventory(total=0, used=0)
        # total is (0 - 0) * 1.0 = 0, so usage should be 0
        self.assertEqual(0, inv.usage)

    def test_limit(self):
        CONF.aardvark.watermark = 80
        inv = make_inventory(total=100, used=50)
        # limit = total * watermark / 100 = 100 * 80 / 100 = 80
        self.assertEqual(80.0, inv.limit)

    def test_excessive_below_watermark(self):
        CONF.aardvark.watermark = 80
        inv = make_inventory(total=100, used=50)
        # usage=50%, watermark=80%, so not excessive
        self.assertEqual(0, inv.excessive)

    def test_excessive_above_watermark(self):
        CONF.aardvark.watermark = 80
        inv = make_inventory(total=100, used=90)
        # usage=90%, watermark=80%
        # excessive = used + reserved - limit = 90 + 0 - 80 = 10
        self.assertEqual(10.0, inv.excessive)

    def test_reserved_attr(self):
        inv = make_inventory(total=100, used=50)
        # self.reserved is set to 0 (reservation for scheduling)
        self.assertEqual(0, inv.reserved)

    def test_reserved_scheduling(self):
        # self.reserved starts at 0 and can be used to reserve scheduling slots
        inv = make_inventory(total=100, used=50)
        inv.reserved = 5
        self.assertEqual(5, inv.reserved)

    def test_repr(self):
        inv = make_inventory(resource_class="VCPU", total=100, used=50)
        r = repr(inv)
        self.assertIn("VCPU", r)
        self.assertIn("100", r)

    def test_to_str(self):
        inv = make_inventory(resource_class="MEMORY_MB", total=200, used=100)
        s = inv.to_str()
        self.assertIn("MEMORY_MB", s)
        self.assertIn("200", s)
