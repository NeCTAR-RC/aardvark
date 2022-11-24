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

import abc

from aardvark import exception

from oslo_log import log as logging

LOG = logging.getLogger(__name__)


def host_potential(host, resources, include_free):
    if include_free:
        return host.free_resources + resources
    return resources


class ReaperStrategy(object, metaclass=abc.ABCMeta):
    """The base Reaper Strategy class

    This is the class that all the Strategies for the Reaper Service have to
    inherit from
    """

    def __init__(self, watermark_mode=False):
        self.watermark_mode = watermark_mode

    @abc.abstractmethod
    def get_preemptible_servers(self, requested, hosts, num_instances,
                                projects=None, flavors=None):
        # NOTE(ttsiouts): Every driver should override this method and
        # implement the strategy of the freeing
        pass

    def check_spots(self, selected_hosts, num_instances):
        # NOTE: If we run out of hosts before the max retries, we need
        # to check if we have enough spots reserved. If not, we won't
        # kill any servers. The least number of reserved spots is the
        # number of the requested instances.
        spots = sum([sh.reserved_spots for sh in selected_hosts])
        LOG.info("Requested %s spots and found %s", num_instances, spots)
        if spots < num_instances:
            message = 'Not enough preemptible resources'
            raise exception.NotEnoughResources(message)
