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

from aardvark.api import keystone
from aardvark.tests import base


class KeystoneClientTests(base.TestCase):
    @mock.patch("aardvark.api.keystone._get_keystone_client")
    def test_get_preemptible_projects(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        fake_project = mock.Mock()
        fake_project.id = "proj-uuid"
        fake_project.name = "preemptible-project"
        mock_client.projects.list.return_value = [fake_project]
        result = keystone.get_preemptible_projects()
        mock_client.projects.list.assert_called_once_with(
            enabled=True, tags=["preemptible"]
        )
        self.assertEqual(1, len(result))
        self.assertEqual("proj-uuid", result[0].id_)
        self.assertEqual("preemptible-project", result[0].name)
        self.assertTrue(result[0].preemptible)

    @mock.patch("aardvark.api.keystone._get_keystone_client")
    def test_get_preemptible_projects_empty(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_client.projects.list.return_value = []
        result = keystone.get_preemptible_projects()
        self.assertEqual([], result)
