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

from aardvark.tests import base

from aardvark.notifications import manager


class ManagerTests(base.TestCase):

    def setUp(self):
        super(ManagerTests, self).setUp()
        self.manager = manager.ListenerManager()

    def _create_mocked_listeners(self, num):
        listeners = []
        for i in range(0, num):
            listener = mock.Mock()
            listener.start = mock.Mock()
            listener.stop = mock.Mock()
            listener.wait = mock.Mock()
            listeners.append(listener)
        return listeners

    def test_manager(self):
        mocked_listeners = self._create_mocked_listeners(2)
        with mock.patch.object(self.manager, '_get_listeners') as mocked:
            mocked.return_value = mocked_listeners
            self.manager.start()
            self.assertEqual(mocked_listeners, self.manager.listeners)
            for listener in mocked_listeners:
                listener.start.assert_called_once()
            self.manager.stop()
            self.assertEqual([], self.manager.listeners)
            for listener in mocked_listeners:
                listener.stop.assert_called_once()
                listener.wait.assert_called_once()
