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


class Resources:
    """Internal representation of resources

    Just a helper class that enables the reaper to make simple calculations
    with resources.
    """

    # NOTE(ttsiouts): Be careful when comparing! Use comparisons only from the
    # pov of the first operand!!!!!
    # e.g. a = {vcpu: 3, memory: 1024}, b = {vcpu: 2, memory: 512}
    # a < b => False and a > b => True and a == b => False

    def __init__(self, resources=None):
        """Initialized with a dictionary of resource classes and values"""
        self.resources = set()
        if resources is None:
            return
        for resource, value in resources.items():
            if value == 0:
                continue
            setattr(self, resource, value)
            self.resources = self.resources | set([resource])

    @staticmethod
    def obj_from_inventories(inventories):
        resources = {}
        for rc, inventory in inventories.items():
            allocation_ratio = inventory["allocation_ratio"]
            reserved = inventory["reserved"]
            total = inventory["total"] * allocation_ratio - reserved
            resources[rc] = total
        return Resources(resources)

    @staticmethod
    def obj_from_flavor(flavor, is_bfv=False):
        vcpus = flavor["vcpus"]
        disk = flavor["ephemeral"] + flavor["disk"] + flavor["swap"]
        ram = flavor["ram"]

        # TODO(ttsiouts): Here we have to check the extra_specs of the flavor
        resources = {}
        if vcpus > 0:
            resources.update({"VCPU": vcpus})
        if disk > 0 and not is_bfv:
            resources.update({"DISK_GB": disk})
        if ram > 0:
            resources.update({"MEMORY_MB": ram})

        return Resources(resources)

    @staticmethod
    def obj_from_payload(flavor, is_bfv=False):
        vcpus = flavor["vcpus"]
        disk = flavor["ephemeral_gb"] + flavor["root_gb"] + flavor["swap"]
        ram = flavor["memory_mb"]

        # TODO(ttsiouts): Here we have to check the extra_specs of the flavor
        resources = {}
        if vcpus > 0:
            resources.update({"VCPU": vcpus})
        if disk > 0 and not is_bfv:
            resources.update({"DISK_GB": disk})
        if ram > 0:
            resources.update({"MEMORY_MB": ram})

        return Resources(resources)

    @staticmethod
    def max_ratio(one, two):
        res = one / two
        return int(max([ratio for ratio in res.values()]))

    @staticmethod
    def min_ratio(one, two):
        res = one / two
        return int(min([ratio for ratio in res.values()]))

    def __add__(self, other):
        resources = self.resources | other.resources
        new = dict()
        for res in resources:
            new[res] = getattr(self, res, 0) + getattr(other, res, 0)
        return Resources(new)

    def __sub__(self, other):
        resources = self.resources | other.resources
        new = dict()
        for res in resources:
            value = getattr(self, res, 0) - getattr(other, res, 0)
            new[res] = int(value)
        return Resources(new)

    def __mul__(self, other):
        # NOTE(ttsiouts): Should be used only with numbers... Resource * 3
        new = dict()
        for res in self.resources:
            try:
                new[res] = int(getattr(self, res, 0) * other)
            except TypeError:
                return None
        return Resources(new)

    def __div__(self, other):
        if isinstance(other, Resources):
            return self._div_with_resource(other)
        elif isinstance(other, int):
            return self._div_with_int(other)
        else:
            raise TypeError

    def _div_with_resource(self, other):
        # NOTE(ttsiouts): the result of this operation is the minimum result
        # after dividing all the resource classes:
        # e.g. a = {vcpu: 100, memory: 1024}, b = {vcpu: 1, memory: 512}
        #      a / b = 2 (because a.memory / b.memory = 2)
        resources = self.resources | other.resources
        return {
            rc: getattr(self, rc, 0) / getattr(other, rc, 1)
            for rc in resources
        }

    def _div_with_int(self, other):
        resources = {}
        for res in self.resources:
            resources.update({res: getattr(self, res) / other})
        return Resources(resources)

    def __eq__(self, other):
        return all(
            [getattr(self, r) == getattr(other, r, 0) for r in self.resources]
        )

    def __ne__(self, other):
        return any(
            [getattr(self, r) != getattr(other, r, 0) for r in self.resources]
        )

    def __gt__(self, other):
        return all(
            [getattr(self, r) > getattr(other, r, 0) for r in self.resources]
        )

    def __lt__(self, other):
        return all(
            [getattr(self, r) < getattr(other, r, 0) for r in self.resources]
        )

    def __ge__(self, other):
        return all(
            [getattr(self, r) >= getattr(other, r, 0) for r in self.resources]
        )

    def __le__(self, other):
        return all(
            [getattr(self, r) <= getattr(other, r, 0) for r in self.resources]
        )

    __truediv__ = __div__

    def __repr__(self):
        text = ", ".join(
            [f"{res}: {getattr(self, res)}" for res in self.resources]
        )
        return f"<Resources({text})>"

    def to_dict(self):
        tdict = dict()
        for resource in self.resources:
            tdict.update({resource: getattr(self, resource)})
        return tdict
