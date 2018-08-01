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


import six
import functools

from oslo_log import log
from oslo_context import context
from oslo_service import service
from oslo_service import periodic_task
from taskflow.utils import threading_utils

import aardvark.conf
from aardvark.reaper import reaper
from aardvark import config
from aardvark.reaper import job_manager
from aardvark.reaper import reaper_request as rr_obj
from aardvark import utils


LOG = log.getLogger(__name__)
CONF = aardvark.conf.CONF


def watermark_enabled(fn):
    @functools.wraps(fn)
    def wrapper(*args, **kwargs):
        if CONF.aardvark.enable_watermark_mode:
            fn(*args, **kwargs)
    return wrapper


class ReaperService(service.Service):

    def __init__(self):
        super(ReaperService, self).__init__()
        if six.PY3:
            # TODO(ttsiouts): Hack to make eventlet work right, remove when the
            # following is fixed: https://github.com/eventlet/eventlet/issues/230
            from taskflow.utils import eventlet_utils as _eu  # noqa
            try:
                import eventlet as _eventlet  # noqa
            except ImportError:
                pass
        self.reaper_instances = []
        self._setup_workers(utils.map_aggregate_names())

    def start(self):
        super(ReaperService, self).start()
        self._start_workers()
        self._start_state_calculation()

    def stop(self, graceful=True):
        self._stop_workers()
        super(ReaperService, self).stop(graceful=graceful)

    def _start_workers(self):
        LOG.info('Starting Reaper workers')
        for instance in self.reaper_instances:
            instance.worker.start()

    def _stop_workers(self):
        LOG.info('Stoping Reaper workers')
        for instance in self.reaper_instances:
            instance.stop_handling()
            instance.worker.join()

    def _setup_workers(self, watched_aggregates):
        if len(watched_aggregates) == 0:
            LOG.debug('One worker for all infrastructure will be started')
            watched_aggregates = [watched_aggregates]

        for aggregates in watched_aggregates:
            if not isinstance(aggregates, list):
                aggregates = [aggregates]
            instance = reaper.Reaper(aggregates)
            instance.worker = threading_utils.daemon_thread(instance.job_handler)
            self.reaper_instances.append(instance)

    @watermark_enabled
    def _start_state_calculation(self):
        self.state_calculator = SystemStateCalculator()
        LOG.info('Starting Periodic System State Calculation')
        admin_context = context.get_admin_context()
        self.tg.add_dynamic_timer(
            self.state_calculator.periodic_tasks,
            periodic_interval_max=CONF.periodic_interval,
            context=admin_context)


class SystemStateCalculator(periodic_task.PeriodicTasks):

    def __init__(self):
        super(SystemStateCalculator, self).__init__(CONF)
        self.watched_aggregates = utils.map_aggregate_names()
        self.job_manager = job_manager.JobManager()

    def periodic_tasks(self, context, raise_on_error=False):
        return self.run_periodic_tasks(context, raise_on_error=raise_on_error)

    @periodic_task.periodic_task(spacing=CONF.periodic_interval,
                                 run_immediately=True)
    def calculate_system_state(self, context, startup=True):
        LOG.debug('Periodic Timer for state check expired ')
        for aggregates in self.watched_aggregates:
            request = rr_obj.StateCalculationRequest(aggregates)
            self.job_manager.post_job(request)


def prepare_service(argv=None):
    log.register_options(CONF)
    log.set_defaults(default_log_levels=CONF.default_log_levels)

    argv = argv or []
    config.parse_args(argv)

    log.setup(CONF, 'aardvark-reaper')