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

from aardvark.db import migration
from aardvark.tests import base


class MigrationTests(base.TestCase):
    def setUp(self):
        super().setUp()
        # Reset the global _IMPL between tests
        migration._IMPL = None

    @mock.patch("stevedore.driver.DriverManager")
    def test_get_backend(self, mock_driver_mgr):
        mock_backend = mock.Mock()
        mock_driver_mgr.return_value.driver = mock_backend
        backend = migration.get_backend()
        self.assertEqual(mock_backend, backend)
        mock_driver_mgr.assert_called_once()

    @mock.patch("stevedore.driver.DriverManager")
    def test_get_backend_cached(self, mock_driver_mgr):
        mock_backend = mock.Mock()
        mock_driver_mgr.return_value.driver = mock_backend
        backend1 = migration.get_backend()
        backend2 = migration.get_backend()
        self.assertEqual(backend1, backend2)
        # Only called once due to caching
        mock_driver_mgr.assert_called_once()

    @mock.patch("aardvark.db.migration.get_backend")
    def test_upgrade(self, mock_get_backend):
        mock_backend = mock.Mock()
        mock_get_backend.return_value = mock_backend
        migration.upgrade("head")
        mock_backend.upgrade.assert_called_once_with("head")

    @mock.patch("aardvark.db.migration.get_backend")
    def test_version(self, mock_get_backend):
        mock_backend = mock.Mock()
        mock_backend.version.return_value = "abc123"
        mock_get_backend.return_value = mock_backend
        result = migration.version()
        self.assertEqual("abc123", result)
        mock_backend.version.assert_called_once_with()

    @mock.patch("aardvark.db.migration.get_backend")
    def test_stamp(self, mock_get_backend):
        mock_backend = mock.Mock()
        mock_get_backend.return_value = mock_backend
        migration.stamp("head")
        mock_backend.stamp.assert_called_once_with("head")

    @mock.patch("aardvark.db.migration.get_backend")
    def test_revision(self, mock_get_backend):
        mock_backend = mock.Mock()
        mock_get_backend.return_value = mock_backend
        migration.revision(message="test message", autogenerate=True)
        mock_backend.revision.assert_called_once_with("test message", True)
