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

from __future__ import division
import itertools

from oslo_log import log as logging

import aardvark.conf
from aardvark.reaper.strategies import utils
from aardvark.reaper import strategy
from aardvark import utils as aardvark_utils


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class StrictStrategy(strategy.ReaperStrategy):

    def __init__(self, watermark_mode):
        super(StrictStrategy, self).__init__(watermark_mode=watermark_mode)

    def get_preemptible_servers(self, requested, hosts, num_instances,
                                projects, flavors=None):
        selected = list()
        selected_hosts = list()

        # This is the maximum number of spots that we'll try to free up
        max_allocs = num_instances * CONF.reaper.alternatives

        for i in range(0, max_allocs):

            # Find all the matching flavor combinations and order them
            combo = self.find_matching_server_combinations(hosts, requested,
                                                           projects)

            if not combo:
                # If we run out of combos before the max retries break and
                # check if we have enough spots reserved.
                LOG.debug('No combo returned.')
                break

            host = combo.provider
            # Reserve the resources to enable us to reuse the host
            host.reserved_spots += 1
            if not combo.instances:
                host.used_resources += requested
            else:
                resources = utils.sum_resources(combo.instances)
                host.used_resources -= resources - requested
                host.preemptible_servers = [
                    pr_server for pr_server in host.preemptible_servers
                    if pr_server not in combo.instances]

            if host not in selected_hosts:
                selected_hosts.append(host)
            selected += combo.instances
            LOG.debug('List of instances: %s from host: %s selected',
                      combo.instances, combo.provider.name)

        if not self.watermark_mode:
            # Watermark mode is best effort. So skip this check in this
            # mode. On the other hand if we are not in watermark mode we
            # free space only if we can find the requested space.
            self.check_spots(selected_hosts, num_instances)

        return selected_hosts, selected

    def find_matching_server_combinations(self, hosts, requested, projects):
        """Find the best matching combination

        The purpose of this feature is to eliminate the idle resources. So the
        best matching combination is the one that makes use of the most
        available space on a host.
        """
        only_free = False
        combinations = list()

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
            LOG.debug("Checing host %s", host.name)
            # NOTE(ttsiouts): If free space is enough for the new server
            # then we should not delete any of the existing servers
            LOG.debug('Requested: %s, Free: %s',
                      requested, host.free_resources)
            if requested <= host.free_resources:
                LOG.debug('Free resources enough. Requested: %s, Free: %s',
                          requested, host.free_resources)
                leftovers = host.free_resources - requested
                combinations.append(utils.Combination(provider=host,
                                                      leftovers=leftovers,
                                                      instances=[]))
                only_free = True
                continue

            preemptible = self.filter_servers(host, requested)
            LOG.debug('Preemptibles: %s', preemptible)
            end = len(preemptible) + 1
            for num in range(1, end):
                num_combinations = itertools.combinations(preemptible, num)
                for combo in num_combinations:
                    resources = (
                        utils.sum_resources(combo) + host.free_resources)
                    if requested <= resources:
                        instances = [x for x in combo]
                        leftovers = resources - requested
                        combinations.append(
                            utils.Combination(provider=host,
                                              leftovers=leftovers,
                                              instances=instances))
                    else:
                        LOG.debug("Requested: %s resources: %s. combo %s, not "
                                  "selected", requested, resources, combo)

        if not combinations:
            return None

        if only_free:
            # NOTE(ttsiouts): if there is a host with free space avoid
            # deleting running VMs.
            combinations = [x for x in combinations if len(x.instances) == 0]

        return utils.sort_combinations(combinations)

    def populate_host(self, host, projects):
        host.populate(projects)

    def filter_servers(self, host, requested):
        return host.preemptible_servers
