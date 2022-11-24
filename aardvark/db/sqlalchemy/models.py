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

import json

from oslo_db.sqlalchemy import models
from oslo_db.sqlalchemy.types import String
from sqlalchemy import Boolean
from sqlalchemy import Column
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import Integer
from sqlalchemy import schema
from sqlalchemy import Text
from sqlalchemy.types import TypeDecorator, TEXT
from sqlalchemy import orm
from urllib import parse as urlparse

import aardvark.conf


CONF = aardvark.conf.CONF


def table_args():
    engine_name = urlparse.urlparse(CONF.database.connection).scheme
    if engine_name == 'mysql':
        return {'mysql_engine': CONF.database.mysql_engine,
                'mysql_charset': "utf8"}
    return None


class JsonEncodedType(TypeDecorator):
    """Abstract base type serialized as json-encoded string in db."""
    type = None
    impl = TEXT

    def process_bind_param(self, value, dialect):
        if value is None:
            # Save default value according to current type to keep the
            # interface the consistent.
            value = self.type()
        elif not isinstance(value, self.type):
            raise TypeError("%(class)s supposes to store "
                            "%(type)s objects, but %(value)s "
                            "given" % {'class': self.__class__.__name__,
                                       'type': self.type.__name__,
                                       'value': type(value).__name__})
        serialized_value = json.dumps(value)
        return serialized_value

    def process_result_value(self, value, dialect):
        if value is not None:
            value = json.loads(value)
        return value


class JSONEncodedDict(JsonEncodedType):
    """Represents dict serialized as json-encoded string in db."""
    type = dict


class JSONEncodedList(JsonEncodedType):
    """Represents list serialized as json-encoded string in db."""
    type = list


class AardvarkBase(models.TimestampMixin,
                   models.ModelBase):

    metadata = None

    def as_dict(self):
        d = {}
        for c in self.__table__.columns:
            d[c.name] = self[c.name]
        return d

    def save(self, session=None):
        import aardvark.db.sqlalchemy.api as db_api

        if session is None:
            session = db_api.get_session()

        super(AardvarkBase, self).save(session)
        session.commit()


Base = declarative_base(cls=AardvarkBase)


class SchedulingEvent(Base):
    """Represents a SchedulingEvent."""

    __tablename__ = 'scheduling_event'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_scheduling0uuid'),
        schema.UniqueConstraint('request_id', name='uniq_req0request_id'),
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    request_spec = Column(JSONEncodedDict)
    request_id = Column(Integer)
    retries = Column(Integer, default=0)


class InstanceSchedulingEvent(Base):
    __tablename__ = 'instance_scheduling_event'
    __table_args__ = (
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    instance_uuid = Column(String(36))
    event_uuid = Column(String(36))
    handled = Column(Boolean, default=False)

    scheduling_event = orm.relationship(
        "SchedulingEvent",
        backref='scheduling_event',
        primaryjoin='and_(InstanceSchedulingEvent.event_uuid == '
                    'SchedulingEvent.uuid)',
        foreign_keys=event_uuid
    )


class StateUpdateEvent(Base):
    """Represents a StateUpdateEvent."""

    __tablename__ = 'state_update_event'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_state_update0uuid'),
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    instance_uuid = Column(String(36))
    state_update = Column(JSONEncodedDict)
    image = Column(String(36))
    flavor = Column(JSONEncodedDict)
    handled = Column(Boolean, default=False)


class ReaperAction(Base):
    """Represents a Reaper Action"""

    __tablename__ = 'reaper_action'
    __table_args__ = (
        schema.UniqueConstraint('uuid', name='uniq_action0uuid'),
        table_args()
    )

    id = Column(Integer, primary_key=True, autoincrement=True)
    uuid = Column(String(36))
    state = Column(String(36))
    requested_instances = Column(JSONEncodedList, nullable=True)
    fault_reason = Column(Text, nullable=True)
    victims = Column(JSONEncodedList, nullable=True)
    event = Column(String(36))
