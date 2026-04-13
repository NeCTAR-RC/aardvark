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

from cinderclient import client
from keystoneauth1 import loading as keystone_loading

import aardvark.conf


CONF = aardvark.conf.CONF


def _get_cinder_client():
    auth_plugin = keystone_loading.load_auth_from_conf_options(CONF, "cinder")
    session = keystone_loading.load_session_from_conf_options(
        CONF, "cinder", auth=auth_plugin
    )
    return client.Client(
        CONF.cinder.client_version,
        session=session,
        region_name=CONF.cinder.region_name,
    )


def get_image_from_volume(volume_id):
    client = _get_cinder_client()
    volume = client.volumes.get(volume_id)
    return volume.volume_image_metadata["image_id"]
