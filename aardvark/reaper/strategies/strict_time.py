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

from oslo_log import log as logging

import aardvark.conf
from aardvark.objects import resources as res_obj
from aardvark.reaper.strategies import strict


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class StrictTimeStrategy(strict.StrictStrategy):
    def __init__(self, watermark_mode):
        super().__init__(watermark_mode=watermark_mode)

    def populate_host(self, host, projects):
        host.populate_sorted(projects)

    def filter_servers(self, host, requested):
        valid_servers = list()
        for fid, instance_list in host.flavors_dict.items():
            if requested <= instance_list[0].resources:
                valid_servers.append(instance_list[0])
            times = res_obj.Resources.min_ratio(
                requested, instance_list[0].resources
            )
            if times <= len(host.flavors_dict[fid]):
                valid_servers += host.flavors_dict[fid][:times]
            else:
                valid_servers += host.flavors_dict[fid]
        return valid_servers
