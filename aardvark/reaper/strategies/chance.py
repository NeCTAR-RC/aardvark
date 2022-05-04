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

import aardvark.conf
from aardvark.objects import resources as resources_obj
from aardvark.reaper import strategy
from aardvark import utils

from oslo_log import log as logging

import random


LOG = logging.getLogger(__name__)
CONF = aardvark.conf.CONF


class ChanceStrategy(strategy.ReaperStrategy):

    def __init__(self, watermark_mode=False):
        super(ChanceStrategy, self).__init__(watermark_mode=watermark_mode)

    def get_preemptible_servers(self, requested, hosts, num_instances,
                                projects, flavors=None):
        """Implements the strategy of freeing up the requested resources.

        :param req_spec: an instance of the RequestSpec class representing the
                         requested resources
        :param resources: (Why is this here?)
        """

        if self.watermark_mode:
            # In the watermark mode we need to go over the hosts until we've
            # gathered enough resources
            max_attempts = len(hosts)
        else:
            # This is the maximum number of spots that we'll try to free up
            max_attempts = num_instances * CONF.reaper.alternatives
        timeout = CONF.reaper.parallel_timeout

        @utils.timeit
        @utils.parallelize(max_results=max_attempts, timeout=timeout)
        def get_valid_hosts(hosts, requested):
            valid_hosts = list()
            for host in hosts:
                if host.disabled:
                    LOG.info("Skipping host %s because it is disabled",
                             host.name)
                    continue
                LOG.debug("Checing host %s", host.name)
                host.populate(projects)
                resources = strategy.host_potential(
                    host, host.preemptible_resources, not self.watermark_mode)
                if requested <= resources:
                    # Create a list with the hosts that can potentially provide
                    # the requested resources.
                    valid_hosts.append(host)
            return valid_hosts

        @utils.timeit
        @utils.parallelize(max_results=len(hosts), timeout=timeout)
        def populate_hosts(hosts, selected_hosts):
            valid = []
            for host in hosts:
                if host in selected_hosts:
                    continue
                host.populate(projects)
                if not host.disabled:
                    valid.append(host)
                else:
                    LOG.info("Skipping host %s because it is disabled",
                             host.name)
            return valid

        selected_servers = list()
        selected_hosts = list()
        gathered = resources_obj.Resources()

        for i in range(0, max_attempts):

            if self.watermark_mode:
                valid = [h for h in populate_hosts(hosts, selected_hosts)]
            else:
                valid = get_valid_hosts(hosts, requested)

            try:
                host = random.choice(valid)
            except IndexError:
                break
            servers = self.select_servers(host, requested)

            # If the host is not added and it has given servers for culling,
            # add it to the list. If a host's available are enough, then the
            # select_servers will return an empty list. But, assume, that the
            # resources were freed up in a previous round of selection. If
            # they were free since the beginning, the reaper would not have
            # been triggered.
            if host not in selected_hosts:
                selected_hosts.append(host)

            selected_servers += servers

            # In case we are in the watermark_mode we should stop as soon as we
            # find enough resources to avoid freeing more than what we actually
            # need.
            if self.watermark_mode:
                for s in servers:
                    gathered += s.resources
                if gathered >= requested:
                    break

        if not self.watermark_mode:
            # Watermark mode is best effort. So skip this check in this
            # mode. On the other hand if we are not in watermark mode we
            # free space only if we can find the requested space.
            self.check_spots(selected_hosts, num_instances)

        return selected_hosts, selected_servers

    def select_servers(self, host, requested):
        """Selects the server(s) to cull from the provided host.

        Returns a list of randomly selected servers to be culled. At the same
        time, it reserves the resources of the selected servers in the host.
        The maximum attempts per host are specified using configuration option
        CONF.chance_driver.max_attempts.

        :param host: the selected host
        """
        max_attempts = CONF.reaper.max_attempts
        # Consider the available resources that the host can provide.
        preemptible = host.preemptible_servers

        selected = list()
        resources = resources_obj.Resources()
        # If the already available are enough, just return an empty list
        host_resources = strategy.host_potential(
            host, resources, not self.watermark_mode)
        if requested <= host_resources:
            host.used_resources += requested
            host.reserved_spots += 1
            return selected

        # Shuffle the servers
        random.shuffle(preemptible)
        gathered_resources = resources_obj.Resources()
        for marker in range(0, max_attempts):
            try:
                server = preemptible[marker]
            except IndexError:
                if not self.watermark_mode:
                    # If we run out of servers we are stopping without killing
                    # any VMs. So returning an empty list
                    selected = list()
                break

            selected.append(server)
            gathered_resources += server.resources

            host_resources = strategy.host_potential(
                host, gathered_resources, not self.watermark_mode)
            if host_resources >= requested:
                # This is the point we want to reach. It means that requested
                # resources will be available after culling selected servers.
                break
        else:
            # If we reach here, then the max_attempts have been reached.
            # If this is not the watermark mode return an empty list since
            # obviously we weren't able to gather the requested resources.
            # The watermark mode is best effort so we need everything we
            # can free up.
            if not self.watermark_mode:
                selected = list()

        # Reserving the selected resources in order to be able to perform
        # further computations if needed. Also we need the number of free
        # spots for the alternatives functionality. This can be inaccurate
        # in the watermark mode. But in the watermark mode we know that the
        # each resource provider will be used only once.

        if len(selected) > 0:
            host.used_resources -= gathered_resources - requested
            host.reserved_spots += 1
            host.preemptible_servers = [
                pr_server for pr_server in host.preemptible_servers
                if pr_server not in selected]

        return selected
