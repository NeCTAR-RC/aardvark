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

from datetime import datetime
from unittest import mock

import aardvark.conf
from aardvark.objects import instance
from aardvark.tests import base


CONF = aardvark.conf.CONF


class InstanceListTests(base.TestCase):

    def setUp(self):
        super(InstanceListTests, self).setUp()
        self.instance_list = instance.InstanceList()

    def _create_mock_instance(self, created, name):
        instance = mock.Mock(created=created)
        type(instance).name = name
        return instance

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 120
        server1 = self._create_mock_instance('2019-07-16T13:13:00Z', 'server1')
        server2 = self._create_mock_instance('2019-07-17T13:15:00Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:00Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:14:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        expected = [server5, server4, server3, server1, server2]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(expected, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_all_reversed(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 120
        server1 = self._create_mock_instance('2019-07-18T14:13:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:13:02Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:03Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:14:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        expected = [server5, server4, server3, server2, server1]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(expected, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_dif(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 120
        server1 = self._create_mock_instance('2019-07-18T14:12:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:13:02Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:03Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:14:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        expected = [server5, server4, server3, server2, server1]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(expected, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_diff(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 120
        server1 = self._create_mock_instance('2019-07-18T14:12:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:13:02Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:03Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:13:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 16, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        expected = [server5, server1, server2, server3, server4]
        expected = [x.name for x in expected]
        result = self.instance_list._sort_instances(instances)
        result = [x.name for x in result]
        self.assertEqual(expected, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_no_sort(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 120
        server1 = self._create_mock_instance('2019-07-18T14:12:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:13:02Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:03Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:13:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 17, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(instances, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_no_quick_kill(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 0
        server1 = self._create_mock_instance('2019-07-18T14:12:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:13:02Z', 'server2')
        server3 = self._create_mock_instance('2019-07-18T14:13:03Z', 'server3')
        server4 = self._create_mock_instance('2019-07-18T14:13:39Z', 'server4')
        server5 = self._create_mock_instance('2019-07-18T14:14:40Z', 'server5')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1, server2, server3, server4, server5]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(instances, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_only_one(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 60
        server1 = self._create_mock_instance('2019-07-18T14:14:01Z', 'server1')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(instances, result)

    @mock.patch('aardvark.utils._get_now')
    def test_sorted_instances_only_two(self, mock_now):
        CONF.aardvark.quick_kill_seconds = 60
        server1 = self._create_mock_instance('2019-07-18T14:13:01Z', 'server1')
        server2 = self._create_mock_instance('2019-07-18T14:14:02Z', 'server2')
        # Already sorted from oldest to newest
        mock_now.return_value = datetime(2019, 7, 18, 14, 15, 0, 0)
        instances = [server1, server2]
        expected = [server2, server1]
        result = self.instance_list._sort_instances(instances)
        self.assertEqual(expected, result)
