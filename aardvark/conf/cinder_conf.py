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

from keystoneauth1 import loading as ks_loading
from oslo_config import cfg


SERVICE_TYPE = 'volumev3'


cinder_group = cfg.OptGroup(
    'cinder',
    title='Cinder Service Options',
    help="Configuration options for connecting to the Cinder API service"
)


cinder_opts = [
    cfg.StrOpt("client_version",
        default="3",
        help="""
Selects where the API microversion requested by the cinderclient.
"""
    ),
]


def register_opts(conf):

    conf.register_group(cinder_group)
    conf.register_opts(cinder_opts, group=cinder_group)

    group = getattr(cinder_group, 'name', cinder_group)

    ks_loading.register_session_conf_options(conf, group)
    ks_loading.register_auth_conf_options(conf, group)

    adapter_opts = get_ksa_adapter_opts(SERVICE_TYPE)
    conf.register_opts(adapter_opts, group=group)


def get_ksa_adapter_opts(default_service_type, deprecated_opts=None):

    opts = ks_loading.get_adapter_conf_options(
        include_deprecated=False, deprecated_opts=deprecated_opts)

    cfg.set_defaults(opts,
                     valid_interfaces=['internal', 'public'],
                     service_type=default_service_type)
    return opts
