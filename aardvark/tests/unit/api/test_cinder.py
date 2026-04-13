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

from aardvark.api import cinder
from aardvark.tests import base


class CinderClientTests(base.TestCase):
    @mock.patch("aardvark.api.cinder._get_cinder_client")
    def test_get_image_from_volume(self, mock_get_client):
        mock_client = mock.Mock()
        mock_get_client.return_value = mock_client
        mock_volume = mock.Mock()
        mock_volume.volume_image_metadata = {"image_id": "fake-image-uuid"}
        mock_client.volumes.get.return_value = mock_volume
        result = cinder.get_image_from_volume("fake-volume-uuid")
        mock_client.volumes.get.assert_called_once_with("fake-volume-uuid")
        self.assertEqual("fake-image-uuid", result)
