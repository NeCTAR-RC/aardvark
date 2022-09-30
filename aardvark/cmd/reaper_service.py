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


import sys

from oslo_cache import core as cache
from oslo_config import cfg
from oslo_log import log
from oslo_service import service
import socket

from aardvark import config


CONF = cfg.CONF
LOG = log.getLogger(__name__)


def main():
    # Parse config file and command line options, then start logging
    prepare_service(sys.argv)

    # Importing after the config is parsed in order to correctly pass
    # the config option to all decorators
    from aardvark.services import reaper_service
    reaper = reaper_service.ReaperService()

    launcher = service.launch(CONF, reaper, restart_method='mutate')
    launcher.wait()


def prepare_service(argv=None):
    # Load the hostname in config in order to use it later
    cache.configure(CONF)

    CONF.host = socket.gethostname()

    log.register_options(CONF)
    log.set_defaults(default_log_levels=CONF.default_log_levels)

    argv = argv or []
    config.parse_args(argv)

    log.setup(CONF, 'aardvark-reaper')
