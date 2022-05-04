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
from aardvark import exception
from aardvark.tests import base
from aardvark import utils


CONF = aardvark.conf.CONF


class UtilsTests(base.TestCase):

    def setUp(self):
        super(UtilsTests, self).setUp()

    def test_retries(self):
        mocked_method = mock.Mock(__name__="mocked",
                                  side_effect=exception.RetryException())
        decorated_mocked_method = utils.retries(
            exception.AardvarkException)(mocked_method)
        self.assertRaises(exception.AardvarkException, decorated_mocked_method)
        self.assertEqual(mocked_method.call_count, 3)

    def test_retries_no_side_effect(self):
        mocked_method = mock.Mock(__name__="mocked",
                                  side_effect=exception.RetryException())
        decorated_mocked_method = utils.retries()(mocked_method)
        decorated_mocked_method()
        self.assertEqual(mocked_method.call_count, 3)

    @mock.patch('aardvark.api.nova.aggregate_list')
    def test_map_aggregate_names(self, mock_agg_list):

        aggregates = [
            mock.Mock(uuid="agg1_uuid"),
            mock.Mock(uuid="agg2_uuid")
        ]
        aggregates[0].name = "agg1"
        aggregates[1].name = "agg2"
        CONF.reaper.watched_aggregates = ["agg1", "agg2"]
        mock_agg_list.return_value = aggregates

        uuids = utils.map_aggregate_names()
        self.assertEqual([["agg1_uuid"], ["agg2_uuid"]], uuids)

    @mock.patch('aardvark.api.nova.aggregate_list')
    def test_map_aggregate_names_bad_config(self, mock_agg_list):

        aggregates = [
            mock.Mock(uuid="agg1_uuid"),
            mock.Mock(uuid="agg2_uuid")
        ]
        aggregates[0].name = "agg1"
        aggregates[1].name = "agg2"
        CONF.reaper.watched_aggregates = ["agg3"]
        mock_agg_list.return_value = aggregates

        self.assertRaises(exception.BadConfigException,
                          utils.map_aggregate_names)

    def test_workload_split(self):

        def assert_gen(expected, actual):
            for exp, act in zip(expected, actual):
                self.assertEqual(exp, tuple(act))
            self.assertEqual(len(expected), len(tuple(actual)))

        load = range(1, 14)
        num_workers = 15
        expected = [(1,), (2,), (3,), (4,), (5,), (6,), (7,), (8,), (9,),
                    (10,), (11,), (12,), (13,)]
        assert_gen(expected, utils.split_workload(num_workers, load))

        load = range(1, 5)
        num_workers = 2
        expected = [(1, 2), (3, 4)]
        assert_gen(expected, utils.split_workload(num_workers, load))

        load = range(1, 6)
        num_workers = 6
        expected = [(1,), (2,), (3,), (4,), (5,)]
        assert_gen(expected, utils.split_workload(num_workers, load))

        load = range(1, 6)
        num_workers = 2
        expected = [(1, 2, 3), (4, 5)]
        assert_gen(expected, utils.split_workload(num_workers, load))

        load = [1, 2]
        num_workers = 7
        expected = [(1,), (2,)]
        assert_gen(expected, utils.split_workload(num_workers, load))

        load = range(1, 10)
        num_workers = 7
        expected = [(1, 2), (3, 4), (5, 6), (7, 8), (9,)]
        assert_gen(expected, utils.split_workload(num_workers, load))

    def test_parallelize_no_args(self):
        @utils.parallelize()
        def serial(a):
            c = []
            for b in a:
                c.append(b + 1)
            return c

        workload = range(1, 11)
        result = serial(workload)
        expected = range(2, 12)
        self.assertEqual(list(expected), sorted(result))

    def test_parallelize_with_args(self):
        @utils.parallelize()
        def serial(a, b):
            c = []
            for d in a:
                c.append((d + 1, b + 1))
            return c

        b = 1
        workload = range(1, 11)
        result = serial(workload, b)
        expected = zip(range(2, 12), [b + 1] * 10)
        self.assertEqual(list(expected), sorted(result))

    def test_parallelize_with_kwargs(self):
        @utils.parallelize()
        def serial(a, b, c=None):
            d = []
            for e in a:
                d.append((e + 1, b + 1, c))
            return d

        b = 1
        workload = range(1, 2)
        result = serial(workload, b, c=20)
        expected = zip(range(2, 3), [b + 1], [20])
        self.assertEqual(list(expected), sorted(result))
