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

from aardvark.objects import capabilities
from aardvark.objects import resource_provider
from aardvark.objects import resources as res_obj


def make_resources(vcpu=0, memory=0, disk=0):

    res_dict = {}
    if vcpu > 0:
        res_dict.update({'VCPU': vcpu})
    if disk > 0:
        res_dict.update({'DISK_GB': disk})
    if memory > 0:
        res_dict.update({'MEMORY_MB': memory})

    return res_obj.Resources(res_dict)


def make_flavor(uuid=None, vcpus=1, ephemeral=0, root_gb=20, swap=0, ram=2000,
                name=None):
    flavor = {
        "uuid": uuid or "fake_uuid",
        "vcpus": vcpus,
        "ephemeral": ephemeral,
        "disk": root_gb,
        "swap": swap,
        "ram": ram,
        "original_name": name or "flavor1"
    }
    return flavor


def make_server(resources=None, uuid=None, flavor=None, flavor_name=None):
    resources = resources or make_resources(vcpu=1, memory=512, disk=10)
    uuid = uuid or 'server1'
    kwargs = {
        'vcpus': getattr(resources, 'VCPU', 0),
        'ram': getattr(resources, 'MEMORY_MB', 0),
        'root_gb': getattr(resources, 'DISK_GB', 0),
        'name': flavor_name
    }

    flavor = flavor or make_flavor(**kwargs)
    return mock.Mock(resources=resources, uuid=uuid, flavor=flavor)


def make_inventory_dict(ratio=1.0, reserved=0, total=10):
    return {
        'allocation_ratio': ratio,
        'reserved': reserved,
        'total': total
    }


def make_capabilities(used=None, total=None):
    used = used or make_resources()
    total = total or make_resources(vcpu=128, memory=20000, disk=80)
    return capabilities.Capabilities(used, total)


def make_resource_provider(uuid=None, name=None, capabilities=None,
                           reserved_spots=0):
    uuid = uuid or 'fake_rp_uuid'
    name = name or 'fake_rp_name'
    capabilities = capabilities or make_capabilities()
    rp = resource_provider.ResourceProvider(uuid, name)
    rp._capabilities = capabilities
    rp.reserved_spots = reserved_spots
    rp.populated = True
    rp._disabled = False
    return rp
