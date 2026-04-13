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

from aardvark.api.rest import placement
from aardvark.objects import resources


def _get_placement_client():
    return placement.PlacementClient()


def get_resource_providers(aggregates=None):
    client = _get_placement_client()
    result = client.resource_providers(aggregates)
    from aardvark.objects import resource_provider as rp_obj

    return [rp_obj.ResourceProvider(rp["uuid"], rp["name"]) for rp in result]


def get_resource_provider_usages(resource_provider):
    client = _get_placement_client()
    result = client.usages(resource_provider)
    return resources.Resources(result)


def get_resource_provider_inventories(resource_provider):
    client = _get_placement_client()
    result = client.inventories(resource_provider)
    return resources.Resources.obj_from_inventories(result)


def get_consumer_allocations(consumer, rp_uuid):
    client = _get_placement_client()
    allocations = client.get_allocations(consumer)["allocations"]
    try:
        alloc_res = allocations[rp_uuid]["resources"]
    except KeyError:
        # This means that the consumer does not have
        # allocations to this resource provider so
        # just return empty resources.
        alloc_res = {}
    return resources.Resources(alloc_res)


def get_resource_classes():
    client = _get_placement_client()
    result = client.resource_classes()
    return result


def get_traits():
    client = _get_placement_client()
    return client.traits()
