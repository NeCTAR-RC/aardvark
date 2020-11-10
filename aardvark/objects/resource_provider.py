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

from aardvark.api import nova
from aardvark.api import placement
from aardvark.objects import base
from aardvark.objects import capabilities
from aardvark.objects import instance
from aardvark.objects import resources

from oslo_log import log


LOG = log.getLogger(__name__)


class ResourceProvider(base.PlacementObject):

    def __init__(self, uuid, name):
        super(ResourceProvider, self).__init__(uuid=uuid, name=name)
        self.uuid = uuid
        self.name = name
        self._hypervisor = None
        self._preemptible_servers = list()
        self._capabilities = None
        self.reserved_spots = 0
        self.populated = False
        self.flavors_dict = collections.defaultdict(list)
        self._disabled = None

    @property
    def usages(self):
        return placement.get_resource_provider_usages(self.uuid)

    @property
    def inventories(self):
        return placement.get_resource_provider_inventories(self.uuid)

    @property
    def resource_classes(self):
        return placement.get_resource_classes()

    @property
    def capabilities(self):
        if not self._capabilities:
            self._capabilities = capabilities.Capabilities(self.usages,
                                                           self.inventories)
        return self._capabilities

    @property
    def preemptible_servers(self):
        return self._preemptible_servers

    @preemptible_servers.setter
    def preemptible_servers(self, new):
        self._preemptible_servers = new
        self.flavors_dict = collections.defaultdict(list)
        for server in new:
            self.flavors_dict[server.flavor['original_name']].append(server)

    @property
    def preemptible_resources(self):
        return sum((server.resources for server in self.preemptible_servers),
                   resources.Resources())

    @property
    def total_resources(self):
        return self.capabilities.total

    @property
    def used_resources(self):
        return self.capabilities.used

    @used_resources.setter
    def used_resources(self, new):
        self.capabilities.used = new

    @property
    def reserved_resources(self):
        return self.capabilities.reserved

    @property
    def free_resources(self):
        return self.capabilities.free_resources

    def __eq__(self, other):
        return self.uuid == other.uuid

    def __hash__(self):
        return hash(self.uuid)

    @property
    def hypervisor(self):
        if self._hypervisor is None:
            hypervisor = nova.hypervisor_get(self.uuid)
            self._hypervisor = hypervisor
        return self._hypervisor

    @property
    def disabled(self):
        if self._disabled is None:
            service_name = self.hypervisor.service.get('host')
            service = nova.service_status(service_name)
            self._disabled = (service.forced_down or service.state != 'up'
                              or service.status != 'enabled')
        return self._disabled

    def populate(self, preemptible_projects):
        if self.disabled:
            return
        if self.populated:
            return
        instance_list = instance.InstanceList()
        servers = list()
        for pr_project in preemptible_projects:
            filters = {
                'host': self.hypervisor.service.get('host'),
                'project_id': pr_project,
                'vm_state': 'ACTIVE'
            }
            servers += instance_list.instances(self.uuid, **filters)
        self.preemptible_servers = servers
        self.populated = True

    def populate_sorted(self, preemptible_projects):
        if self.disabled:
            return
        if self.populated:
            return
        instance_list = instance.InstanceList()
        servers = list()
        for pr_project in preemptible_projects:
            filters = {
                'host': self.hypervisor.service.get('host'),
                'project_id': pr_project,
                'vm_state': 'ACTIVE'
            }
            servers += instance_list.sorted_instances(self.uuid, **filters)
        self.preemptible_servers = servers
        self.populated = True

    def __repr__(self):
        return '<ResourceProvider(name: %s, uuid: %s)>' % (self.name,
                                                           self.uuid)


class ResourceProviderList(base.PlacementObject):

    def __init__(self, aggregates=None):
        super(ResourceProviderList, self).__init__(aggregates=aggregates)
        self.aggregates = aggregates

    @property
    def resource_providers(self):
        return placement.get_resource_providers(self.aggregates)
