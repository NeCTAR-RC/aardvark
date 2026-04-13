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


SERVICE_TYPE = "placement"


placement_group = cfg.OptGroup(
    "placement",
    title="Placement Service Options",
    help="Configuration options for connecting to the placement API service",
)


def register_opts(conf):
    conf.register_group(placement_group)

    group = getattr(placement_group, "name", placement_group)

    ks_loading.register_session_conf_options(conf, group)
    ks_loading.register_auth_conf_options(conf, group)

    adapter_opts = get_ksa_adapter_opts(SERVICE_TYPE)
    conf.register_opts(adapter_opts, group=group)


def get_ksa_adapter_opts(default_service_type, deprecated_opts=None):
    opts = ks_loading.get_adapter_conf_options(
        include_deprecated=False, deprecated_opts=deprecated_opts
    )

    cfg.set_defaults(
        opts,
        valid_interfaces=["internal", "public"],
        service_type=default_service_type,
    )
    return opts
