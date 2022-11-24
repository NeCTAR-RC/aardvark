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

from oslo_db import exception as db_exc
from oslo_db.sqlalchemy import session as db_session
from oslo_utils import uuidutils
from sqlalchemy import orm
from sqlalchemy.orm.exc import NoResultFound

import aardvark.conf
from aardvark.db import api
from aardvark.db.sqlalchemy import models
from aardvark import exception


CONF = aardvark.conf.CONF
_FACADE = None


def _create_facade_lazily():
    global _FACADE
    if _FACADE is None:
        _FACADE = db_session.EngineFacade.from_config(CONF)
    return _FACADE


def get_engine():
    facade = _create_facade_lazily()
    return facade.get_engine()


def get_session(**kwargs):
    facade = _create_facade_lazily()
    return facade.get_session(**kwargs)


def get_backend():
    return Connection()


def model_query(model, *args, **kwargs):
    session = kwargs.get('session') or get_session()
    query = session.query(model, *args)
    return query


class Connection(api.Connection):
    """Base class for storage connections."""

    def __init__(self):
        pass

    def create_scheduling_event(self, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()

        event = models.SchedulingEvent()
        event.update(values)
        try:
            event.save()
        except db_exc.DBDuplicateEntry:
            raise exception.SchedulingEventAlreadyExists()
        return event

    def create_instance_scheduling_event(self, values):
        event = models.InstanceSchedulingEvent()
        event.update(values)
        try:
            event.save()
        except db_exc.DBDuplicateEntry:
            uuid = values['instance_uuid']
            raise exception.InstanceSchedulingEventAlreadyExists(uuid=uuid)
        return event

    def update_scheduling_event(self, event_uuid, values):
        session = get_session()
        with session.begin():
            query = model_query(models.SchedulingEvent, session=session)
            query = query.filter_by(uuid=event_uuid)
            try:
                ref = query.with_for_update('update').one()
            except NoResultFound:
                raise exception.SchedulingEventNotFound(uuid=event_uuid)
            ref.update(values)
        return ref

    def get_instance_scheduling_event(self, instance_uuid, handled=False):
        query = model_query(models.InstanceSchedulingEvent)
        query = query.filter_by(instance_uuid=instance_uuid)
        query = query.filter_by(handled=handled)
        query = query.options(
            orm.Load(models.InstanceSchedulingEvent).joinedload('*'))
        try:
            return query.one()
        except NoResultFound:
            raise exception.SchedulingEventNotFound(uuid=instance_uuid)

    def get_scheduling_event_by_request_id(self, request_id):
        query = model_query(models.SchedulingEvent)
        query = query.filter_by(request_id=request_id)
        try:
            return query.one()
        except NoResultFound:
            raise exception.SchedulingEventNotFound(uuid=request_id)

    def list_scheduling_event_instances(self, event_uuid):
        query = model_query(models.InstanceSchedulingEvent)
        query = query.filter_by(event_uuid=event_uuid)
        try:
            return query.all()
        except NoResultFound:
            raise exception.InstanceSchedulingEventNotFound(uuid=event_uuid)

    def update_instance_scheduling_event(self, scheduling_event_uuid, values,
                                         instance_uuid=None):
        session = get_session()
        with session.begin():
            query = model_query(models.InstanceSchedulingEvent,
                                session=session)
            query = query.filter_by(event_uuid=scheduling_event_uuid)
            if instance_uuid:
                query = query.filter_by(instance_uuid=instance_uuid)
            try:
                references = query.with_for_update('update').all()
            except NoResultFound:
                raise exception.InstanceSchedulingEventNotFound(
                    uuid=scheduling_event_uuid)
            for ref in references:
                ref.update(values)
        return ref

    def count_instance_scheduling_events(self, scheduling_event_uuid, handled):
        query = model_query(models.InstanceSchedulingEvent)
        query = query.filter_by(event_uuid=scheduling_event_uuid)
        query = query.filter_by(handled=handled)
        return query.count()

    def create_state_update_event(self, values):
        if not values.get('uuid'):
            values['uuid'] = uuidutils.generate_uuid()
        event = models.StateUpdateEvent()
        event.update(values)
        try:
            event.save()
        except db_exc.DBDuplicateEntry:
            raise exception.StateUpdateEventAlreadyExists()
        return event

    def get_state_update_event_by_instance(self, instance_uuid, handled=False):
        query = model_query(models.StateUpdateEvent)
        query = query.filter_by(instance_uuid=instance_uuid)
        query = query.filter_by(handled=handled)
        try:
            return query.one()
        except NoResultFound:
            raise exception.StateUpdateEventNotFound(uuid=instance_uuid)

    def get_state_update_event_by_uuid(self, uuid):
        query = model_query(models.StateUpdateEvent)
        query = query.filter_by(uuid=uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.StateUpdateEventNotFound(uuid=uuid)

    def update_instance_state_update_event(self, event_uuid, instance_uuid,
                                           values):
        session = get_session()
        with session.begin():
            query = model_query(models.StateUpdateEvent, session=session)
            query = query.filter_by(uuid=event_uuid)
            query = query.filter_by(instance_uuid=instance_uuid)
            try:
                ref = query.with_for_update('update').one()
            except NoResultFound:
                raise exception.StateUpdateEventNotFound(uuid=event_uuid)
            ref.update(values)
        return ref

    def create_reaper_action(self, values):
        if 'uuid' not in values:
            values['uuid'] = uuidutils.generate_uuid()
        action = models.ReaperAction()
        action.update(values)
        try:
            action.save()
        except db_exc.DBDuplicateEntry:
            raise exception.ReaperActionAlreadyExists()
        return action

    def get_reaper_action_by_uuid(self, uuid):
        query = model_query(models.ReaperAction)
        query = query.filter_by(uuid=uuid)
        try:
            return query.one()
        except NoResultFound:
            raise exception.ReaperActionNotFound(uuid=uuid)

    def list_reaper_actions(self):
        query = model_query(models.ReaperAction)
        try:
            return query.all()
        except NoResultFound:
            return []

    def get_reaper_action_by_instance(self, uuid):
        uuid_like = "%%%s%%" % uuid
        query = model_query(models.ReaperAction)
        query = query.filter(
            models.ReaperAction.requested_instances.contains([uuid_like]))
        return query.all()

    def get_reaper_action_by_victim(self, uuid):
        uuid_like = "%%%s%%" % uuid
        query = model_query(models.ReaperAction)
        query = query.filter(models.ReaperAction.victims.contains([uuid_like]))
        return query.all()

    def update_reaper_action(self, uuid, values):
        session = get_session()
        with session.begin():
            query = model_query(models.ReaperAction, session=session)
            query = query.filter_by(uuid=uuid)
            try:
                ref = query.with_for_update('update').one()
            except NoResultFound:
                raise exception.ReaperActionNotFound(uuid=uuid)
            ref.update(values)
        return ref
