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

import oslo_cache

from aardvark.api import nova
import aardvark.conf
from aardvark.objects import base


CONF = aardvark.conf.CONF


class Flavor(base.BaseObject):

    def __init__(self, id, name, preemptible=False):
        self.id = id
        self.name = name
        self.preemptible = preemptible


class FlavorList(base.BaseObject):

    def __init__(self):
        super(FlavorList, self).__init__()
        cache_region = oslo_cache.create_region()
        self.cache = oslo_cache.configure_cache_region(
            CONF, cache_region)

    @property
    def preemptible_flavors(self):
        CACHE_KEY = 'aardvark:flavors'
        flavors = self.cache.get(CACHE_KEY)
        if not flavors:
            flavors = [Flavor(flavor.id, flavor.name, True)
                       for flavor in nova.get_preemptible_flavors()]
            self.cache.set(CACHE_KEY, flavors)
        return flavors
