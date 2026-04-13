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

CONF = aardvark.conf.CONF


class Inventory:
    _attrs = ["used", "max_unit", "step_size", "min_unit", "total"]

    def __init__(self, resource_class, **kwargs):
        self.resource_class = resource_class

        allocation_ratio = kwargs["allocation_ratio"]
        reserved = kwargs["reserved"]

        for attr in self._attrs:
            try:
                if attr == "total":
                    total = float(kwargs[attr] - reserved) * allocation_ratio
                    setattr(self, attr, total)
                    continue
                setattr(self, attr, float(kwargs[attr]))
            except KeyError:
                setattr(self, attr, 0.0)

        # This is going to be used just to reserve resources while scheduling
        # multiple VMs.
        self.reserved = 0

    @property
    def free(self):
        return self.total - self.used

    @property
    def usage(self):
        if self.total:
            return self.used * 100 / self.total
        return 0

    @property
    def limit(self):
        return (self.total * CONF.aardvark.watermark) / 100

    @property
    def excessive(self):
        if self.usage <= CONF.aardvark.watermark:
            return 0
        else:
            return self.used + self.reserved - self.limit

    def __add__(self, other):
        kwargs = {
            "used": self.used + other.used,
            "reserved": self.reserved + other.reserved,
            "total": self.total + other.total,
        }
        return Inventory(self.resource_class, **kwargs)

    def __repr__(self):
        return self.to_str()

    def to_str(self):
        return f"<Inventory: {self.resource_class}: total: {self.total} , used: {self.used + self.reserved}, usage: {self.usage}%>"
