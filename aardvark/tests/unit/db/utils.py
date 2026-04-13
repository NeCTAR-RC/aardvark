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

from aardvark.db import api as db_api


def get_test_reaper_action(**kw):
    requested = ["5d12f6fd-a196-4bf0-ae4c-1f639a523a52"]
    victims = ["5d12f6fd-a196-4bf0-ae4c-1f639a523a53"]
    return {
        "id": kw.get("id", 12),
        "uuid": kw.get("uuid", "483203a3-dbee-4a9c-9d65-9820512f4df8"),
        "state": kw.get("state", "SUCCESS"),
        "requested_instances": kw.get("requested_instances", requested),
        "fault_reason": kw.get("fault_reason", None),
        "victims": kw.get("victims", victims),
        "event": kw.get("event", "BUILD_REQUEST"),
    }


def create_test_reaper_action(**kw):
    action = get_test_reaper_action(**kw)
    if "id" not in kw:
        del action["id"]
    dbapi = db_api.get_instance()
    return dbapi.create_reaper_action(action)
