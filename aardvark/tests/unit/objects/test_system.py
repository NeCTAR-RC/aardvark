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

from aardvark.objects import system
from aardvark.tests import base
from aardvark.tests.unit.objects import fakes as object_fakes


class SystemTests(base.TestCase):
    def setUp(self):
        super().setUp()

    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_system_state(
        self, mock_flavor_list, mock_project_list, mock_rp_list
    ):
        used1 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        total1 = object_fakes.make_resources(vcpu=8, memory=2048, disk=40)
        caps1 = object_fakes.make_capabilities(used=used1, total=total1)

        used2 = object_fakes.make_resources(vcpu=2, memory=512, disk=10)
        total2 = object_fakes.make_resources(vcpu=4, memory=1024, disk=20)
        caps2 = object_fakes.make_capabilities(used=used2, total=total2)

        rp1 = object_fakes.make_resource_provider(
            uuid="1", name="rp1", capabilities=caps1
        )
        rp2 = object_fakes.make_resource_provider(
            uuid="2", name="rp2", capabilities=caps2
        )

        mock_rp_list.return_value.resource_providers = [rp1, rp2]
        mock_project_list.return_value.preemptible_projects = []
        mock_flavor_list.return_value.preemptible_flavors = []

        s = system.System()
        state = s.system_state()
        self.assertIsNotNone(state)

    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_resource_providers(
        self, mock_flavor_list, mock_project_list, mock_rp_list
    ):
        rp1 = object_fakes.make_resource_provider(uuid="1", name="rp1")
        mock_rp_list.return_value.resource_providers = [rp1]
        mock_project_list.return_value.preemptible_projects = []
        mock_flavor_list.return_value.preemptible_flavors = []

        s = system.System()
        rps = s.resource_providers
        self.assertEqual([rp1], rps)

    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_preemptible_projects(
        self, mock_flavor_list, mock_project_list, mock_rp_list
    ):
        mock_project = mock.Mock(id_="proj-uuid")
        mock_rp_list.return_value.resource_providers = []
        mock_project_list.return_value.preemptible_projects = [mock_project]
        mock_flavor_list.return_value.preemptible_flavors = []

        s = system.System()
        projects = s.preemptible_projects
        self.assertEqual([mock_project], projects)

    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_preemptible_flavors(
        self, mock_flavor_list, mock_project_list, mock_rp_list
    ):
        mock_flavor = mock.Mock(id="flavor-uuid")
        mock_rp_list.return_value.resource_providers = []
        mock_project_list.return_value.preemptible_projects = []
        mock_flavor_list.return_value.preemptible_flavors = [mock_flavor]

        s = system.System()
        flavors = s.preemptible_flavors
        self.assertEqual([mock_flavor], flavors)

    @mock.patch("aardvark.objects.system.instance.InstanceList")
    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_populate_system_rps(
        self,
        mock_flavor_list,
        mock_project_list,
        mock_rp_list,
        mock_instance_list,
    ):
        mock_project = mock.Mock(id_="proj-uuid")
        rp1 = object_fakes.make_resource_provider(uuid="1", name="rp1")
        mock_server = mock.Mock()
        mock_server.flavor = {"original_name": "m1.small"}
        mock_instance_list.return_value.instances.return_value = [mock_server]

        mock_rp_list.return_value.resource_providers = [rp1]
        mock_project_list.return_value.preemptible_projects = [mock_project]
        mock_flavor_list.return_value.preemptible_flavors = []

        s = system.System()
        s.populate_system_rps()
        self.assertEqual([mock_server], rp1.preemptible_servers)

    @mock.patch(
        "aardvark.objects.system.resource_provider.ResourceProviderList"
    )
    @mock.patch("aardvark.objects.system.project.ProjectList")
    @mock.patch("aardvark.objects.system.flavor.FlavorList")
    def test_projects(self, mock_flavor_list, mock_project_list, mock_rp_list):
        mock_project = mock.Mock(id_="proj-uuid")
        mock_rp_list.return_value.resource_providers = []
        mock_project_list.return_value.projects = [mock_project]
        mock_flavor_list.return_value.preemptible_flavors = []

        s = system.System()
        projects = s.projects
        self.assertEqual([mock_project], projects)
