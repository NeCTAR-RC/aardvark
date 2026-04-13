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

import aardvark.conf
from aardvark.objects import instance
from aardvark.tests import base


CONF = aardvark.conf.CONF


class InstanceTests(base.TestCase):
    def _make_instance(
        self,
        uuid="inst-uuid",
        name="inst-name",
        flavor=None,
        user_id="user1",
        metadata=None,
        image="image-uuid",
        created="2019-01-01T00:00:00Z",
        rp_uuid="rp-uuid",
    ):
        flavor = flavor or {"vcpus": 2, "ram": 512, "disk": 10}
        metadata = metadata or {}
        return instance.Instance(
            uuid, name, flavor, user_id, metadata, image, created, rp_uuid
        )

    def test_init(self):
        inst = self._make_instance()
        self.assertEqual("inst-uuid", inst.uuid)
        self.assertEqual("inst-name", inst.name)
        self.assertEqual("user1", inst.user_id)
        self.assertEqual("image-uuid", inst.image)
        self.assertEqual("rp-uuid", inst.rp_uuid)

    def test_image_none_for_empty_string(self):
        inst = self._make_instance(image="")
        self.assertIsNone(inst.image)

    def test_is_bfv_with_image(self):
        inst = self._make_instance(image="image-uuid")
        self.assertFalse(inst.is_bfv)

    def test_is_bfv_without_image(self):
        inst = self._make_instance(image="")
        self.assertTrue(inst.is_bfv)

    def test_owner_from_metadata(self):
        inst = self._make_instance(
            metadata={"landb-responsible": "responsible@example.com"}
        )
        self.assertEqual("responsible@example.com", inst.owner)

    def test_owner_from_user_id(self):
        inst = self._make_instance(user_id="user123", metadata={})
        self.assertEqual("user123", inst.owner)

    def test_repr(self):
        inst = self._make_instance(uuid="inst-uuid")
        r = repr(inst)
        self.assertIn("inst-uuid", r)

    @mock.patch("aardvark.api.placement.get_consumer_allocations")
    def test_resources_from_placement(self, mock_get_allocs):
        CONF.aardvark.resources_from_flavor = False
        from aardvark.objects import resources as res_obj

        mock_resources = res_obj.Resources({"VCPU": 2})
        mock_get_allocs.return_value = mock_resources
        inst = self._make_instance()
        result = inst.resources
        self.assertEqual(mock_resources, result)
        mock_get_allocs.assert_called_once_with("inst-uuid", "rp-uuid")

    @mock.patch("aardvark.objects.resources.Resources.obj_from_flavor")
    def test_resources_from_flavor(self, mock_from_flavor):
        CONF.aardvark.resources_from_flavor = True
        from aardvark.objects import resources as res_obj

        mock_resources = res_obj.Resources({"VCPU": 2})
        mock_from_flavor.return_value = mock_resources
        flavor = {
            "vcpus": 2,
            "ram": 512,
            "disk": 10,
            "original_name": "m1.small",
        }
        inst = self._make_instance(flavor=flavor)
        result = inst.resources
        self.assertEqual(mock_resources, result)

    @mock.patch("aardvark.api.placement.get_consumer_allocations")
    def test_resources_cached(self, mock_get_allocs):
        CONF.aardvark.resources_from_flavor = False
        from aardvark.objects import resources as res_obj

        mock_resources = res_obj.Resources({"VCPU": 2})
        mock_get_allocs.return_value = mock_resources
        inst = self._make_instance()
        _ = inst.resources
        _ = inst.resources
        # Should only call once (cached)
        mock_get_allocs.assert_called_once()


class InstanceListTests(base.TestCase):
    def setUp(self):
        super().setUp()
        self.instance_list = instance.InstanceList()

    @mock.patch("aardvark.api.nova.server_list")
    def test_instances(self, mock_server_list):
        mock_server = mock.Mock()
        mock_server.id = "server-uuid"
        mock_server.name = "server-name"
        mock_server.flavor = {"vcpus": 2}
        mock_server.user_id = "user1"
        mock_server.metadata = {}
        mock_server.image = "image-uuid"
        mock_server.created = "2019-01-01T00:00:00Z"
        mock_server_list.return_value = [mock_server]

        result = self.instance_list.instances(
            rp_uuid="rp-uuid", project_id="proj1"
        )
        self.assertEqual(1, len(result))
        self.assertEqual("server-uuid", result[0].uuid)
        self.assertEqual("rp-uuid", result[0].rp_uuid)
        # should have all_tenants=True since project_id is in filters
        call_kwargs = mock_server_list.call_args[1]
        self.assertTrue(call_kwargs.get("all_tenants", False))

    @mock.patch("aardvark.api.nova.server_list")
    def test_instances_with_flavor_filter(self, mock_server_list):
        mock_server = mock.Mock()
        mock_server.id = "server-uuid"
        mock_server.name = "server-name"
        mock_server.flavor = {"vcpus": 2}
        mock_server.user_id = "user1"
        mock_server.metadata = {}
        mock_server.image = "image-uuid"
        mock_server.created = "2019-01-01T00:00:00Z"
        mock_server_list.return_value = [mock_server]

        self.instance_list.instances(flavor="flavor-id")
        call_kwargs = mock_server_list.call_args[1]
        self.assertTrue(call_kwargs.get("all_tenants", False))

    @mock.patch("aardvark.api.nova.server_list")
    def test_sorted_instances(self, mock_server_list):
        CONF.aardvark.quick_kill_seconds = 0
        mock_server = mock.Mock()
        mock_server.id = "server-uuid"
        mock_server.name = "server-name"
        mock_server.flavor = {"vcpus": 2}
        mock_server.user_id = "user1"
        mock_server.metadata = {}
        mock_server.image = "image-uuid"
        mock_server.created = "2019-01-01T00:00:00Z"
        mock_server_list.return_value = [mock_server]

        result = self.instance_list.sorted_instances("rp-uuid")
        self.assertEqual(1, len(result))

    @mock.patch("aardvark.api.nova.server_delete")
    def test_delete_instance(self, mock_server_delete):
        inst = mock.Mock()
        self.instance_list.delete_instance(inst)
        mock_server_delete.assert_called_once_with(inst)
