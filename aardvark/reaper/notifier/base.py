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


import abc


class BaseNotifier(object, metaclass=abc.ABCMeta):
    """The base class for notifiers

    This is the class where all the aardvark notifiers will inherit from
    """

    def __init__(self):
        pass

    @abc.abstractmethod
    def notify_about_instance(self, instance):
        pass

    def notify_about_action(self, action):
        # Notifiers should implement this if they are meant to
        # notify for a reaper action
        pass

    @property
    def name(self):
        return self.__class__.__name__
