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

from __future__ import print_function

import argparse
import enum
from oslo_config import cfg
import prettytable

from aardvark.reaper import reaper_action as ra


CONF = cfg.CONF


class ReaperActions(object):

    allowed_actions = ['list', 'show']

    @staticmethod
    def list(requested=None, victim=None):

        field_names = ['Started At', 'UUID', 'State', 'Event']

        if requested:
            if victim:
                print("NOTE: \"victim\" param will not be used")
            reaper_actions = ra.ReaperAction.get_by_instance_uuid(requested)
        elif victim:
            reaper_actions = ra.ReaperAction.get_by_victim_uuid(victim)
        else:
            reaper_actions = ra.ReaperAction.list_reaper_actions()

        t = prettytable.PrettyTable(field_names)
        for action in reaper_actions:
            fields = [action.created_at, action.uuid, action.state.value,
                      action.event.value]
            t.add_row(fields)
        print(t)

    @staticmethod
    def show(uuid):
        field_names = ['Property', 'Value']
        action = ra.ReaperAction.get_by_uuid(uuid)
        fields = ['Created At', 'Updated At', 'UUID', 'State',
                  'Requested Instances', 'Victims', 'Event']

        if action.state in (ra.ActionState.FAILED, ra.ActionState.CANCELED):
            fields.append('Fault Reason')

        t = prettytable.PrettyTable(field_names)
        t.align = 'l'

        for field in fields:
            prop = field.lower().replace(' ', '_')
            value = getattr(action, prop, None)
            if isinstance(value, list):
                value = ', '.join(value)
            if isinstance(value, enum.Enum):
                value = value.value
            row = [field, value]
            t.add_row(row)
        print(t)


handlers = {
    'reaper_action': ReaperActions
}


def add_command_parsers(subparsers):
    # TODO(ttsiouts): Implement a maintainable framework
    parser = subparsers.add_parser('reaper_action')
    sub = parser.add_subparsers(dest='action')
    pa = sub.add_parser('list')
    pa.add_argument('--requested', metavar='<requested>', dest='requested')
    pa.add_argument('--victim')
    pa.set_defaults(action_fn=ReaperActions.list)
    pa.set_defaults(action_kwargs=['requested', 'victim'])
    pa.add_argument('action_args', nargs='*', help=argparse.SUPPRESS)

    pa = sub.add_parser('show')
    pa.add_argument('--uuid', metavar='<uuid>', dest='uuid')
    pa.set_defaults(action_fn=ReaperActions.show)
    pa.set_defaults(action_kwargs=['uuid'])
    pa.add_argument('action_args', nargs='*', help=argparse.SUPPRESS)


category = cfg.SubCommandOpt('category',
                             title='Command categories',
                             help='Available categories',
                             handler=add_command_parsers)


def main():
    CONF.register_cli_opts([category])
    CONF(project='aardvark')
    kwargs = {}
    for kwarg in CONF.category.action_kwargs:
        kwargs[kwarg] = getattr(CONF.category, kwarg)
    args = []
    for arg in CONF.category.action_args:
        args.append(args)
    CONF.category.action_fn(*args, **kwargs)
