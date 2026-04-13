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


class Capabilities:
    """Representation of the capabilities of a resource_provider

    Just a helper class that enables the reaper to make simple calculations
    with resources.
    """

    def __init__(self, used, total):
        self.used = used
        self.total = total
        self.reserved = resources.Resources()

    @property
    def free_resources(self):
        return self.total - self.used

    def __add__(self, other):
        used = self.used + other.used
        total = self.total + other.total
        return Capabilities(used, total)

    def usage(self):
        return resources.Resources.max_ratio(self.used * 100, self.total)

    def get_excessive_resources(self, limit):
        excessive = self.used - self.total * (limit / 100.0)
        _dict = excessive.to_dict()
        return resources.Resources(
            {rc: val for rc, val in _dict.items() if val > 0}
        )

    def __repr__(self):
        return f"<Capabilities(used: {self.used}, total: {self.total})>"
