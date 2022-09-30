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
from keystoneclient import client

import aardvark.conf


CONF = aardvark.conf.CONF


def _get_keystone_client():
    auth_plugin = keystone_loading.load_auth_from_conf_options(
        CONF, 'identity')
    session = keystone_loading.load_session_from_conf_options(
        CONF, 'identity', auth=auth_plugin)
    return client.Client(session=session,
                         region_name=CONF.identity.region_name)


def get_preemptible_projects():
    client = _get_keystone_client()
    from aardvark.objects import project as pr_obj
    return [pr_obj.Project(project.id, project.name, True)
            for project in client.projects.list(
                    enabled=True, tags=['preemptible'])]
