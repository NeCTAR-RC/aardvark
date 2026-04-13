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


from aardvark.reaper.notifier import base
from aardvark.reaper.notifier import email_notifier
from aardvark.reaper.notifier import log_notifier
from aardvark.reaper.notifier import oslo_notifier


BaseNotifier = base.BaseNotifier
EmailNotifier = email_notifier.EmailNotifier
LogNotifier = log_notifier.LogNotifier
OsloNotifier = oslo_notifier.OsloNotifier

__all__ = (BaseNotifier, EmailNotifier, LogNotifier, OsloNotifier)
