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

from oslo_config import cfg


reaper_notifier_group = cfg.OptGroup(
    "reaper_notifier",
    title="Aardvark Notifiers Options",
    help="Configuration options for Aardvark notifiers",
)

reaper_notifier_opts = [
    cfg.ListOpt(
        "enabled_notifiers",
        default=["log"],
        help="""
This specifies a list of notifiers to be used upon deleting an instance. The
possible options would be the following:

* log:   Uses python logging to log the action
* oslo:  Sends a standard OpenStack notification
* email: Emails the owner of the instance (To use this option more config
                                           options are needed)
""",
    ),
    cfg.StrOpt(
        "sender",
        help="""
Specifies the sender of the email to the owner(s) of the instance. This option
is required for email notifier only.
""",
    ),
    cfg.StrOpt(
        "smtp_server",
        help="""
Specifies the body of the email to the owner(s) of the instance. This option
is required for email notifier only.
""",
    ),
    cfg.StrOpt(
        "smtp_password",
        default=None,
        secret=True,
        help="""
Specifies the password for connecting to the smtp server. This option
is taken into account only when email notifier is used.
""",
    ),
    cfg.ListOpt(
        "cc",
        default=[],
        help="""
Specifies the addresses to be cc'd in the email to the owner(s) of the
instance. This option is taken into account only when email notifier is used.
""",
    ),
    cfg.ListOpt(
        "bcc",
        default=[],
        help="""
Specifies the addresses to be bcc'd in the email to the owner(s) of the
instance. This is supposed to be used by operators that want to keep a copy of
the emails sent by the service to the users. At the same time if this config
option is set, then Aardvark will send a debug email when an action fails,
containing the action, the triggering request as well as the traceback of the
raised exception. This option is taken into account only when email notifier
is used.
""",
    ),
    cfg.StrOpt(
        "subject",
        default="""
Preemptible instance <instance_uuid> was terminated
""",
        help="""
Specifies the subject of the email to the owner(s) of the instance. The user
can add the following tags and aardvark will format the body with the
information of the instance that is being terminated:
* <user_id>: will be replaced by the owner of the instance
* <instance_name>: will be replaced by the name of the instance
* <instance_uuid>: will be replaced by the uuid of the instance
This option is taken into account only when email notifier is used.
""",
    ),
    cfg.StrOpt(
        "body",
        default="""
Dear <user_id>,

Your preemptible instance with id: <instance_uuid> was terminated.

Aardvark
""",
        help="""
Specifies the body of the email to the owner(s) of the instance. The user can
add the following tags and aardvark will format the body with the information
of the instance that is being terminated:
* <user_id>: will be replaced by the owner of the instance
* <instance_name>: will be replaced by the name of the instance
* <instance_uuid>: will be replaced by the uuid of the instance
This option is taken into account only when email notifier is used.
""",
    ),
    cfg.StrOpt(
        "default_email_domain",
        help="""
If the address found from the instance does not match the email regex, then
aardvark will fall back to this email domain. It should be in this format:
"@example.com". This option is taken into account only when email notifier is
used.
""",
    ),
    cfg.ListOpt(
        "oslo_topics",
        default=[],
        help="""
Specifies the topics where the reaper notifications will be sent.
This option is taken into account only when oslo notifier is used.
""",
    ),
]


def register_opts(conf):
    conf.register_group(reaper_notifier_group)
    conf.register_opts(reaper_notifier_opts, group=reaper_notifier_group)
