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

from aardvark.cmd import db_manage
from aardvark.tests import base


class DbManageTests(base.TestCase):
    @mock.patch("aardvark.db.migration.version")
    def test_do_version(self, mock_version):
        mock_version.return_value = "abc123"
        # Should not raise
        db_manage.do_version()
        mock_version.assert_called_once()

    @mock.patch("aardvark.db.migration.upgrade")
    def test_do_upgrade(self, mock_upgrade):
        with mock.patch("aardvark.cmd.db_manage.CONF") as mock_conf:
            mock_conf.command.revision = "head"
            db_manage.do_upgrade()
        mock_upgrade.assert_called_once_with("head")

    @mock.patch("aardvark.db.migration.stamp")
    def test_do_stamp(self, mock_stamp):
        with mock.patch("aardvark.cmd.db_manage.CONF") as mock_conf:
            mock_conf.command.revision = "abc123"
            db_manage.do_stamp()
        mock_stamp.assert_called_once_with("abc123")

    @mock.patch("aardvark.db.migration.revision")
    def test_do_revision(self, mock_revision):
        with mock.patch("aardvark.cmd.db_manage.CONF") as mock_conf:
            mock_conf.command.message = "test msg"
            mock_conf.command.autogenerate = True
            db_manage.do_revision()
        mock_revision.assert_called_once_with(
            message="test msg", autogenerate=True
        )

    def test_add_command_parsers(self):
        mock_subparsers = mock.Mock()
        mock_parser = mock.Mock()
        mock_subparsers.add_parser.return_value = mock_parser
        db_manage.add_command_parsers(mock_subparsers)
        # Four subcommands: version, upgrade, stamp, revision
        self.assertEqual(4, mock_subparsers.add_parser.call_count)
        calls = [c[0][0] for c in mock_subparsers.add_parser.call_args_list]
        self.assertIn("version", calls)
        self.assertIn("upgrade", calls)
        self.assertIn("stamp", calls)
        self.assertIn("revision", calls)
