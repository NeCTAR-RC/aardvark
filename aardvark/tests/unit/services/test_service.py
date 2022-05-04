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
from aardvark.services import reaper_service
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes as reaper_fakes


CONF = aardvark.conf.CONF


class ReaperServiceTests(base.TestCase):

    def setUp(self):
        super(ReaperServiceTests, self).setUp()

    @mock.patch('aardvark.utils.map_aggregate_names')
    @mock.patch('aardvark.reaper.job_manager.JobManager')
    def test_system_calculator(self, job_man, aggregates_map):
        aggs = [['agg1'], ['agg2']]
        aggregates_map.return_value = aggs
        calculator = reaper_service.SystemStateCalculator()
        calculator.calculate_system_state(None)
        requests = [
            reaper_fakes.make_calculation_request(aggregates=a) for a in aggs
        ]
        calculator.job_manager.post_job.assert_has_calls([
            mock.call(req) for req in requests
        ], any_order=True)

    @mock.patch('aardvark.reaper.reaper.Reaper')
    @mock.patch('taskflow.utils.threading_utils')
    def test_worker_health_check(self, mocked_utils, mocked_reaper):
        aggs = [['agg1'], ['agg2']]
        instances = [
            mock.Mock(aggregates=agg, missed_acks=0) for agg in aggs
        ]
        checker = reaper_service.ReaperWorkerHealthCheck([
            ins for ins in instances
        ])
        for i in range(1, 7):
            checker.check_worker_state(None)
            for instance in checker.reaper_instances:
                self.assertEqual(i, instance.missed_acks)

        # Now the workers are considered to be dead and get revived
        checker.check_worker_state(None)
        for instance in instances:
            self.assertTrue(instance.stop_handling.called)
            self.assertTrue(instance.worker.join.called)
            self.assertNotIn(instance, checker.reaper_instances)
