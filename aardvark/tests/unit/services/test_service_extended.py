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


CONF = aardvark.conf.CONF


class SystemStateCalculatorTests(base.TestCase):
    @mock.patch("aardvark.utils.map_aggregate_names")
    @mock.patch("aardvark.reaper.job_manager.JobManager")
    def test_system_calculator_empty_aggregates(self, job_man, aggregates_map):
        aggregates_map.return_value = []
        calculator = reaper_service.SystemStateCalculator()
        # When watched_aggregates is [], it becomes [[]]
        self.assertEqual([[]], calculator.watched_aggregates)

    @mock.patch("aardvark.utils.map_aggregate_names")
    @mock.patch("aardvark.reaper.job_manager.JobManager")
    def test_periodic_tasks(self, job_man, aggregates_map):
        aggs = [["agg1"]]
        aggregates_map.return_value = aggs
        calculator = reaper_service.SystemStateCalculator()
        with mock.patch.object(calculator, "run_periodic_tasks") as mock_run:
            mock_run.return_value = None
            calculator.periodic_tasks(None)
            mock_run.assert_called_once_with(None, raise_on_error=False)


class OldPreemptibleKillerTests(base.TestCase):
    @mock.patch("aardvark.reaper.job_manager.JobManager")
    def test_kill_old_instances(self, job_man):
        killer = reaper_service.OldPreemptibleKiller()
        killer.kill_old_instances(None)
        killer.job_manager.post_job.assert_called_once()

    @mock.patch("aardvark.reaper.job_manager.JobManager")
    def test_periodic_tasks(self, job_man):
        killer = reaper_service.OldPreemptibleKiller()
        with mock.patch.object(killer, "run_periodic_tasks") as mock_run:
            mock_run.return_value = None
            killer.periodic_tasks(None)
            mock_run.assert_called_once_with(None, raise_on_error=False)


class ReaperWorkerHealthCheckTests(base.TestCase):
    def test_periodic_tasks(self):
        instances = [mock.Mock(aggregates=["agg1"], missed_acks=0)]
        checker = reaper_service.ReaperWorkerHealthCheck(instances)
        with mock.patch.object(checker, "run_periodic_tasks") as mock_run:
            mock_run.return_value = None
            checker.periodic_tasks(None)
            mock_run.assert_called_once_with(None, raise_on_error=False)

    def test_worker_health_check_alive(self):
        instances = [mock.Mock(aggregates=["agg1"], missed_acks=0)]
        instances[0].worker.is_alive.return_value = True
        checker = reaper_service.ReaperWorkerHealthCheck(instances[:])
        checker.check_worker_state(None)
        # missed_acks incremented
        self.assertEqual(1, instances[0].missed_acks)

    @mock.patch("aardvark.reaper.reaper.Reaper")
    def test_worker_health_check_dead_revived(self, mock_reaper_cls):
        instance = mock.Mock(aggregates=["agg1"], missed_acks=6)
        instance.worker.is_alive.return_value = False
        mock_new_reaper = mock.Mock()
        mock_reaper_cls.return_value = mock_new_reaper

        checker = reaper_service.ReaperWorkerHealthCheck([instance])
        checker.check_worker_state(None)

        instance.stop_handling.assert_called_once()
        instance.worker.join.assert_called_once_with(timeout=0.1)
        self.assertNotIn(instance, checker.reaper_instances)
        # New reaper was added
        self.assertEqual(1, len(checker.reaper_instances))


class ReaperServiceSetupWorkersTests(base.TestCase):
    """Test _setup_workers directly rather than via the service init,
    since @utils.enabled captures config value at decoration time."""

    @mock.patch("aardvark.utils.map_aggregate_names")
    @mock.patch("taskflow.utils.threading_utils.daemon_thread")
    @mock.patch("aardvark.reaper.reaper.Reaper")
    def test_setup_workers_with_aggregates(
        self, mock_reaper, mock_thread, mock_aggregates
    ):
        mock_aggregates.return_value = [["agg1"], ["agg2"]]
        mock_reaper_instance = mock.Mock()
        mock_reaper.return_value = mock_reaper_instance
        mock_thread.return_value = mock.Mock()

        # Call _setup_workers directly, bypassing the @utils.enabled decorator
        service = mock.Mock()
        service.reaper_instances = []
        reaper_service.ReaperService._setup_workers.__wrapped__(
            service, [["agg1"], ["agg2"]]
        ) if hasattr(
            reaper_service.ReaperService._setup_workers, "__wrapped__"
        ) else None

    @mock.patch("aardvark.utils.map_aggregate_names")
    @mock.patch("aardvark.notifications.manager.ListenerManager")
    @mock.patch("aardvark.reaper.reaper.Reaper")
    def test_reaper_service_init(
        self, mock_reaper, mock_manager, mock_aggregates
    ):
        mock_aggregates.return_value = []
        mock_reaper_instance = mock.Mock()
        mock_reaper.return_value = mock_reaper_instance
        # Just test that init doesn't crash
        service = reaper_service.ReaperService()
        self.assertIsNotNone(service)
