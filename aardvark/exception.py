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

from oslo_log import log as logging


LOG = logging.getLogger(__name__)


class AardvarkException(Exception):
    """Base Reaper Exception"""

    message = "Unknown error occurred during Reaper's execution"

    def __init__(self, message=None, **kwargs):
        if message:
            self.message = message
        try:
            self.message = self.message % kwargs
        except Exception:
            ex_name = self.__class__.__name__
            LOG.exception(
                "Exception in string format operation, exception type: %s, kwargs: %s",
                ex_name,
                kwargs,
            )
        super().__init__(self.message)


class RetryException(AardvarkException):
    """Generic Exception for the retries mechanism"""

    message = ""


class RetriesExceeded(AardvarkException):
    """Exception raised optionally from the retries mechanism"""

    message = ""


class BadConfigException(AardvarkException):
    """Generic Exception raised by bad configuration"""

    message = "Unknown error occurred because of bad configuration"


class ParallelTimeout(AardvarkException):
    message = "The timeout for a parallel task exceeded"


class ReaperException(AardvarkException):
    """Base Reaper Exception"""

    message = "Unknown error occurred during Reaper's execution"


class NotEnoughResources(ReaperException):
    message = "Unknown error occurred while trying to make space"


class PreemptibleRequest(ReaperException):
    message = "Making space only for non-preemptible reqs."


class UnwatchedAggregate(ReaperException):
    message = "Received request for unwatched aggregate."


class UnknownRequestType(ReaperException):
    message = "Received request of unknown type."


class DBException(AardvarkException):
    """Base DB Exception"""

    message = "An error occurred while accessing the database."


class SchedulingEventAlreadyExists(DBException):
    message = "Scheduling event already exists."


class InstanceSchedulingEventAlreadyExists(DBException):
    message = "Found an unhandled scheduling event for instance %(uuid)s"


class SchedulingEventNotFound(DBException):
    message = "Scheduling event for instance %(uuid)s not found."


class StateUpdateEventAlreadyExists(DBException):
    message = "Found an unhandled state update event for instance %(uuid)s."


class StateUpdateEventNotFound(DBException):
    message = "State update event for instance %(uuid)s was not found."


class ReaperActionAlreadyExists(DBException):
    message = "Reaper action already exists."


class ReaperActionNotFound(DBException):
    message = "Reaper action with uuid %(uuid)s not found."
