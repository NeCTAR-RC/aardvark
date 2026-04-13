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


import collections

from oslo_log import log as logging

import aardvark.conf
from aardvark.objects import resources as res_obj


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


Combination = collections.namedtuple(
    "Combination", "provider instances leftovers"
)


def sum_resources(x):
    resources = res_obj.Resources()
    for y in x:
        resources += y.resources
    return resources


def sort_combinations(combinations):
    """Sorts the found combinations of servers"""
    resources = sorted(
        [
            ("VCPU", CONF.reaper.vcpu_sorting_priority),
            ("MEMORY_MB", CONF.reaper.ram_sorting_priority),
            ("DISK_GB", CONF.reaper.disk_sorting_priority),
        ],
        key=lambda x: x[1],
    )

    for resource, _ in resources:
        combinations = sorted(
            combinations, key=lambda x: getattr(x.leftovers, resource, 0)
        )
        minimum_value = getattr(combinations[0].leftovers, resource, 0)
        combinations = [
            combo
            for combo in combinations
            if getattr(combo.leftovers, resource, 0) == minimum_value
        ]
        if len(combinations) == 1:
            break
    return combinations[0]
