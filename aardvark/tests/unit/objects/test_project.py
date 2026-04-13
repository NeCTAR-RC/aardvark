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

from aardvark.objects import project
from aardvark.tests import base


class ProjectTests(base.TestCase):
    def test_project_init(self):
        p = project.Project("proj-id", "preemptible-project", preemptible=True)
        self.assertEqual("proj-id", p.id_)
        self.assertEqual("preemptible-project", p.name)
        self.assertTrue(p.preemptible)

    def test_project_default_preemptible(self):
        p = project.Project("proj-id", "project")
        self.assertFalse(p.preemptible)


class ProjectListTests(base.TestCase):
    @mock.patch("aardvark.api.keystone.get_preemptible_projects")
    def test_preemptible_projects(self, mock_get_projects):
        mock_project = mock.Mock()
        mock_project.id_ = "proj-uuid"
        mock_project.name = "preemptible-project"
        mock_get_projects.return_value = [mock_project]

        pl = project.ProjectList()
        result = pl.preemptible_projects
        self.assertEqual([mock_project], result)
        mock_get_projects.assert_called_once()

    @mock.patch("aardvark.api.keystone.get_preemptible_projects")
    def test_preemptible_projects_empty(self, mock_get_projects):
        mock_get_projects.return_value = []
        pl = project.ProjectList()
        result = pl.preemptible_projects
        self.assertEqual([], result)
