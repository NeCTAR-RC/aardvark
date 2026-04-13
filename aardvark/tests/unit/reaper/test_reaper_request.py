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

from aardvark.reaper import reaper_request
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


class ReaperRequestTests(base.TestCase):
    def setUp(self):
        super().setUp()

    def _make_request(self):
        return fakes.make_reaper_request()

    def assert_requests(self, request1, request2, attributes):
        for attribute in attributes:
            self.assertEqual(
                getattr(request1, attribute), getattr(request2, attribute)
            )

    def test_request(self):
        request1 = self._make_request()
        to_dict = request1.to_dict()
        request2 = reaper_request.request_from_job(to_dict)
        self.assert_requests(request1, request2, set(to_dict.keys()))


class StateCalculationRequestTests(ReaperRequestTests):
    def setUp(self):
        super().setUp()

    def _make_request(self):
        return fakes.make_calculation_request()
