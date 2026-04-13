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

from aardvark import exception
from aardvark.reaper import reaper_request
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


class OldInstanceKillerRequestTests(base.TestCase):
    def test_request(self):
        request = reaper_request.OldInstanceKillerRequest()
        self.assertEqual("OldInstanceKillerRequest", request.req_type)
        d = request.to_dict()
        self.assertEqual("OldInstanceKillerRequest", d["req_type"])

    def test_from_primitive(self):
        request = reaper_request.OldInstanceKillerRequest.from_primitive(
            {"req_type": "OldInstanceKillerRequest"}
        )
        self.assertIsInstance(request, reaper_request.OldInstanceKillerRequest)

    def test_request_from_job(self):
        d = {"req_type": "OldInstanceKillerRequest"}
        result = reaper_request.request_from_job(d)
        self.assertIsInstance(result, reaper_request.OldInstanceKillerRequest)


class ReaperRequestEqualityTests(base.TestCase):
    def test_reaper_request_equality(self):
        request1 = fakes.make_reaper_request(uuids=["u1"], aggregates=["agg1"])
        request2 = fakes.make_reaper_request(uuids=["u1"], aggregates=["agg1"])
        self.assertEqual(request1, request2)

    def test_state_calculation_request_equality(self):
        r1 = reaper_request.StateCalculationRequest(["agg1"])
        r2 = reaper_request.StateCalculationRequest(["agg1"])
        self.assertEqual(r1, r2)

    def test_state_calculation_from_primitive(self):
        r = reaper_request.StateCalculationRequest.from_primitive(
            {"req_type": "StateCalculationRequest", "aggregates": ["agg1"]}
        )
        self.assertEqual(["agg1"], r.aggregates)

    def test_unknown_request_type_raises(self):
        self.assertRaises(
            exception.UnknownRequestType,
            reaper_request.request_from_job,
            {"req_type": "UnknownType"},
        )
