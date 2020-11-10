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

import itertools
import operator

from oslo_log import log as logging

import aardvark.conf
from aardvark.reaper.strategies import utils
from aardvark.reaper import strategy
from aardvark import utils as aardvark_utils
from aardvark.objects import resources

LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class OldestStrategy(strategy.ReaperStrategy):

    def __init__(self, watermark_mode):
        super().__init__(watermark_mode=watermark_mode)

    def get_preemptible_servers(self, requested, hosts, num_instances,
                                projects):
        selected = list()
        selected_hosts = list()
        seleceted = []
        
        # Find all the matching flavor combinations and order them
        instances = self.find_matching_instances(hosts, projects)
        instances = sorted(instances, key=operator.attrgetter("created"))
        removed_resources = resources.Resources()
        for instance in instances:
            LOG.debug(selected)
            removed_resources += instance.resources
            selected.append(instance)
            if removed_resources > requested:
                LOG.debug("Found enough")
                break

        return [], selected

    def find_matching_instances(self, hosts, projects):
        """Find the best matching combination

        The purpose of this feature is to eliminate the idle resources. So the
        best matching combination is the one that makes use of the most
        available space on a host.
        """
        instances = []
        timeout = CONF.reaper.parallel_timeout

        @aardvark_utils.timeit
        @aardvark_utils.parallelize(max_results=len(hosts), timeout=timeout)
        def populate_hosts(hosts):
            valid = []
            for host in hosts:
                if host.disabled:
                    LOG.info("Skipping host %s because it is disabled",
                             host.name)
                    continue
                self.populate_host(host, projects)
                valid.append(host)
            return valid

        valid = [h for h in populate_hosts(hosts)]

        for host in valid:
            LOG.debug("Checking host %s", host.name)
            instances += self.filter_servers(host)

        LOG.debug(instances)
        return instances

    def populate_host(self, host, projects):
        host.populate(projects)

    def filter_servers(self, host):
        return host.preemptible_servers
