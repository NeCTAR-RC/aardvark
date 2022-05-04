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

from aardvark.api import nova
from aardvark.api import placement
import aardvark.conf
from aardvark.objects import base
from aardvark.objects import resources
from aardvark import utils

from oslo_log import log


LOG = log.getLogger(__name__)


CONF = aardvark.conf.CONF


class Instance(base.BaseObject):

    def __init__(self, uuid, name, flavor, user_id, metadata, image, created,
                 rp_uuid):
        super(Instance, self).__init__(uuid, name, flavor, user_id, metadata,
                                       image, created, rp_uuid)
        self.uuid = uuid
        self.name = name
        self.flavor = flavor
        self.user_id = user_id
        self.metadata = metadata
        self.image = None if image == '' else image
        self.rp_uuid = rp_uuid
        self._resources = None
        self.created = created

    @property
    def resources(self):
        if not self._resources:
            if CONF.aardvark.resources_from_flavor:
                self._resources = self._resources_from_flavor()
            else:
                self._resources = self._resources_from_placement()
        return self._resources

    def _resources_from_placement(self):
        return placement.get_consumer_allocations(self.uuid, self.rp_uuid)

    def _resources_from_flavor(self):
        return resources.Resources.obj_from_flavor(self.flavor,
                                                   is_bfv=self.is_bfv)

    @property
    def owner(self):
        return self.metadata.get('landb-responsible', self.user_id)

    @property
    def is_bfv(self):
        # It's safe to assume that if the image is None then
        # the server is most probably booting from volume
        return self.image is None

    def __repr__(self):
        return '<Instance(uuid: %s)>' % (self.uuid)


class InstanceList(base.BaseObject):

    def __init__(self):
        super(InstanceList, self).__init__()

    def instances(self, rp_uuid=None, **filters):
        if 'flavor' in filters or 'project_id' in filters:
            filters.update({'all_tenants': True})
        if 'sort_dir' not in filters:
            filters['sort_dir'] = 'asc'
        if 'sort_key' not in filters:
            filters['sort_key'] = 'created_at'
        return [Instance(server.id, server.name, server.flavor, server.user_id,
                         server.metadata, server.image, server.created,
                         rp_uuid)
                for server in nova.server_list(**filters)]

    def sorted_instances(self, rp_uuid, **filters):
        return self._sort_instances(self.instances(rp_uuid, **filters))

    def delete_instance(self, instance):
        nova.server_delete(instance)

    def _sort_instances(self, instances):
        # NOTE(ttsiouts): We aim to have instances sorted by creation time
        # from Nova API, from longest living to sortest living. So here
        # we want to put the instances that are alive for less than the
        # configured time in front of the list.
        if CONF.aardvark.quick_kill_seconds == 0:
            return instances
        index = len(instances)
        for instance in reversed(instances):
            lived = utils.seconds_since(instance.created)
            if lived < CONF.aardvark.quick_kill_seconds:
                index = instances.index(instance)
            else:
                break
        if index == 0:
            instances = [x for x in reversed(instances)]
        elif index == len(instances) - 1:
            instances = [instances[index]] + instances[:index]
        elif index < len(instances):
            quick_kill = [x for x in reversed(instances[index - 1:])]
            instances = quick_kill + instances[:index - 1]
        LOG.debug('order now is: %s', ', '.join([x.name for x in instances]))
        return instances
