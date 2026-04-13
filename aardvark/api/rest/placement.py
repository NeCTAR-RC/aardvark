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

from keystoneauth1 import exceptions as keystone_exc
from keystoneauth1 import loading as keystone_loading
import random

import aardvark.conf


CONF = aardvark.conf.CONF


def exception_map(f):
    """Catches keystone exceptions

    Wrapper that tries to catch exceptions from keystone and map them to
    aardvark equivalents.
    """

    def wrapper(self, *a, **k):
        try:
            return f(self, *a, **k)
        except keystone_exc.NotFound:
            # TODO(ttsiouts): map the exceptions
            return None

    return wrapper


class PlacementClient:
    """Client class for querying Placement API"""

    keystone_filter = {
        "service_type": "placement",
        "region_name": CONF.placement.region_name,
    }

    def __init__(self):
        self.client = self._create_client()

    def _create_client(self):
        """Creates the client to Placement API"""
        auth_plugin = keystone_loading.load_auth_from_conf_options(
            CONF, "placement"
        )
        client = keystone_loading.load_session_from_conf_options(
            CONF, "placement", auth=auth_plugin
        )
        client.additional_headers = {"accept": "application/json"}
        return client

    def _get(self, url, obj=None, version="1.17", **kwargs):
        response = self.client.get(
            url, endpoint_filter=self.keystone_filter, microversion=version
        )
        return response.json()

    @exception_map
    def resource_providers(self, aggregates=None):
        """Returns the resource providers from Placement API

        :param aggregates: A dictionary of filters to be passes to Placement
                           If None, returns all the RPs in the system
        """
        filter_str = ""
        if aggregates:
            filter_str = "?member_of=in:" + ",".join(aggregates)
        url = f"/resource_providers{filter_str}"
        resource_providers = self._get(url)
        random.shuffle(resource_providers["resource_providers"])
        return resource_providers["resource_providers"]

    @exception_map
    def usages(self, resource_provider):
        """Returns the usages of a given provider

        :param resource_provider: the provider to search for
        """
        url = f"/resource_providers/{resource_provider}/usages"
        response = self._get(url)
        return response["usages"]

    @exception_map
    def inventory(self, resource_provider_uuid, resource_class):
        """Returns the resource providers from Placement API

        :param filters: A dictionary of filters to be passes to Placement API
                        If None, returns all the RPs in the system
        """
        url = f"/resource_providers/{resource_provider_uuid}/inventories/{resource_class}"
        response = self._get(url)
        return response

    @exception_map
    def inventories(self, resource_provider_uuid):
        """Returns the resource providers from Placement API

        :param filters: A dictionary of filters to be passes to Placement API
                        If None, returns all the RPs in the system
        """
        url = f"/resource_providers/{resource_provider_uuid}/inventories"
        response = self._get(url)
        return response["inventories"]

    @exception_map
    def resource_classes(self):
        url = "/resource_classes"
        resource_classes = self._get(url)
        return resource_classes["resource_classes"]

    @exception_map
    def all_inventories(self):
        """Returns the resource providers from Placement API

        : param filters: A dictionary of filters to be passes to Placement API
                         If None, returns all the RPs in the system
        """
        url = "/resource_providers/inventories"
        inventories = self._get(url)
        return inventories

    @exception_map
    def project_usages(self, project_id, user_id=None):
        """Returns the usages of a given provider

        :param resource_provider: the provider to search for
        """
        url = f"/usages?project_id={project_id}"
        if user_id is not None:
            url += f"&user_id={user_id}"
        response = self._get(url)
        return response["usages"]

    @exception_map
    def traits(self):
        """Returns the usages of a given provider

        :param resource_provider: the provider to search for
        """
        url = "/traits"
        response = self._get(url)
        return response["traits"]

    @exception_map
    def get_allocations(self, consumer):
        """Returns allocations for the provided consumer

        :param consumer: the consumer id to get the allocations for
        """
        url = f"/allocations/{consumer}"
        return self._get(url)
