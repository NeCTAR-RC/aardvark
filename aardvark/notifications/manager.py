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

import aardvark.conf
from aardvark.notifications import endpoints as endpoint_objs
import oslo_messaging


CONF = aardvark.conf.CONF


class ListenerManager:
    def __init__(self):
        self.listeners = []

    def _get_listeners(self):
        targets = [
            oslo_messaging.Target(topic=topic)
            for topic in CONF.notification.topics
        ]
        endpoints = [
            endpoint_objs.SchedulingEndpoint(),
            endpoint_objs.StateUpdateEndpoint(),
        ]
        transports = [
            oslo_messaging.get_notification_transport(CONF, url)
            for url in CONF.notification.urls
        ]
        executor = CONF.notification.executor
        return [
            oslo_messaging.get_notification_listener(
                transport,
                targets,
                endpoints,
                executor=executor,
                allow_requeue=True,
            )
            for transport in transports
        ]

    def start(self):
        self.listeners = self._get_listeners()
        for listener in self.listeners:
            listener.start()

    def stop(self):
        for listener in self.listeners:
            listener.stop()
            listener.wait()
        self.listeners = []
