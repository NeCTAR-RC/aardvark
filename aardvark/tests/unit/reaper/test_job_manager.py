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
from aardvark.reaper import job_manager
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class JobManagerTests(base.TestCase):
    def setUp(self):
        super().setUp()

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_init_single_threaded(self, mock_aggregates):
        CONF.reaper.is_multithreaded = False
        mock_aggregates.return_value = []
        with mock.patch("aardvark.reaper.reaper.Reaper"):
            jm = job_manager.JobManager()
            self.assertTrue(hasattr(jm, "reaper_instance"))

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_init_multithreaded(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        mock_aggregates.return_value = []
        jm = job_manager.JobManager()
        self.assertFalse(hasattr(jm, "reaper_instance"))

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_init_with_aggregates(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        mock_aggregates.return_value = [["agg1"], ["agg2"]]
        jm = job_manager.JobManager()
        self.assertEqual(["agg1", "agg2"], jm.watched_aggregates)

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_init_with_nested_aggregates(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        # Test single aggregate (not list) gets converted
        mock_aggregates.return_value = ["agg1", "agg2"]
        jm = job_manager.JobManager()
        self.assertEqual(["agg1", "agg2"], jm.watched_aggregates)

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_single_threaded_handling(self, mock_aggregates):
        CONF.reaper.is_multithreaded = False
        mock_aggregates.return_value = []
        with mock.patch("aardvark.reaper.reaper.Reaper") as mock_reaper_cls:
            mock_reaper = mock.Mock()
            mock_reaper_cls.return_value = mock_reaper
            jm = job_manager.JobManager()
            request = fakes.make_reaper_request()
            jm.single_threaded_handling(request)
            mock_reaper.handle_request.assert_called_once_with(request)

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_post_job_single_threaded(self, mock_aggregates):
        CONF.reaper.is_multithreaded = False
        mock_aggregates.return_value = []
        with mock.patch("aardvark.reaper.reaper.Reaper") as mock_reaper_cls:
            mock_reaper = mock.Mock()
            mock_reaper_cls.return_value = mock_reaper
            jm = job_manager.JobManager()
            request = fakes.make_reaper_request()
            jm.post_job(request)
            mock_reaper.handle_request.assert_called_once_with(request)

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_is_aggregate_watched_empty(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        mock_aggregates.return_value = []
        jm = job_manager.JobManager()
        request = mock.Mock()
        request.aggregates = []
        # No exception, no modification when watched_aggregates is empty
        result = jm._is_aggregate_watched(request)
        self.assertIsNone(result)

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_is_aggregate_watched_unwatched(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        mock_aggregates.return_value = [["agg1"]]
        jm = job_manager.JobManager()
        request = mock.Mock()
        request.aggregates = ["agg2"]
        self.assertRaises(
            exception.UnwatchedAggregate,
            jm._is_aggregate_watched,
            request,
        )

    @mock.patch("aardvark.utils.map_aggregate_names")
    def test_is_aggregate_watched_common(self, mock_aggregates):
        CONF.reaper.is_multithreaded = True
        mock_aggregates.return_value = [["agg1"]]
        jm = job_manager.JobManager()
        request = mock.Mock()
        request.aggregates = ["agg1", "agg2"]
        jm._is_aggregate_watched(request)
        self.assertEqual(["agg1"], request.aggregates)
