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

from unittest import mock

from aardvark.cmd import reaper_service
from aardvark.tests import base


class PrepareServiceTests(base.TestCase):
    @mock.patch("aardvark.config.parse_args")
    @mock.patch("oslo_log.log.setup")
    @mock.patch("oslo_log.log.set_defaults")
    @mock.patch("oslo_log.log.register_options")
    @mock.patch("oslo_cache.core.configure")
    def test_prepare_service(
        self, mock_cache, mock_reg, mock_set_defaults, mock_setup, mock_parse
    ):
        reaper_service.prepare_service([])
        mock_cache.assert_called_once()
        mock_reg.assert_called_once()
        mock_parse.assert_called_once_with([])
        mock_setup.assert_called_once()

    @mock.patch("aardvark.config.parse_args")
    @mock.patch("oslo_log.log.setup")
    @mock.patch("oslo_log.log.set_defaults")
    @mock.patch("oslo_log.log.register_options")
    @mock.patch("oslo_cache.core.configure")
    def test_prepare_service_with_argv(
        self, mock_cache, mock_reg, mock_set_defaults, mock_setup, mock_parse
    ):
        argv = ["--config-file", "/etc/aardvark.conf"]
        reaper_service.prepare_service(argv)
        mock_parse.assert_called_once_with(argv)
