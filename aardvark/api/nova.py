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

from keystoneauth1 import loading as keystone_loading
from novaclient import client
from oslo_log import log as logging

import aardvark.conf


CONF = aardvark.conf.CONF
LOG = logging.getLogger(__name__)


def _get_nova_client():
    auth_plugin = keystone_loading.load_auth_from_conf_options(
        CONF, 'compute')
    session = keystone_loading.load_session_from_conf_options(
        CONF, 'compute', auth=auth_plugin)
    return client.Client(CONF.compute.client_version, session=session,
                         region_name=CONF.compute.region_name)


def server_delete(server_id):
    """Deletes the given server"""
    client = _get_nova_client()
    server = client.servers.get(server_id)
    task_state = getattr(server, 'OS-EXT-STS:task_state')
    if task_state == 'powering-off':
        LOG.info("Skipping deleting, server powering-off, %s", server.id)
        return False
    if server.status == 'SHUTOFF':
        LOG.info("Unlocking and deleting shutoff server %s", server.id)
        try:
            server.unlock()
        except Exception:
            pass
        server.delete()
        return True

    LOG.info("Stopping and locking server %s", server.id)
    server.stop()
    server.lock(reason="Preemptible pending deletion")
    return False


def server_rebuild(server, image):
    """Rebuilds the given server"""
    client = _get_nova_client()
    return client.servers.rebuild(server, image)


def server_reset_state(server):
    """Resets the given server to ERROR"""
    client = _get_nova_client()
    return client.servers.reset_state(server)


def server_list(**filters):
    """Returns a list of servers matching the given filters"""
    client = _get_nova_client()
    return client.servers.list(search_opts=filters)


def aggregate_list():
    """Returns a list of aggregates"""
    client = _get_nova_client()
    return client.aggregates.list()


def service_status(host, binary=None):
    binary = binary or "nova-compute"
    client = _get_nova_client()
    return client.services.list(host, binary)[0]


def hypervisor_get(uuid):
    client = _get_nova_client()
    return client.hypervisors.get(uuid)
