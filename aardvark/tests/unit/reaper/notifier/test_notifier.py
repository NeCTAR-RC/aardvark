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

import base64
import email
import mock

import aardvark.conf
from aardvark.reaper import notifier
from aardvark.reaper import reaper_action as ra
from aardvark.tests import base
from aardvark.tests.unit.reaper import fakes


CONF = aardvark.conf.CONF


class ReaperNotifierTests(base.TestCase):

    notifier_name = ""

    def setUp(self):
        super(ReaperNotifierTests, self).setUp()
        self.notifier = None

    def test_notifier_name(self):
        if self.notifier:
            self.assertEqual(self.notifier_name, self.notifier.name)


class LogNotifierTests(ReaperNotifierTests):

    notifier_name = "LogNotifier"

    def setUp(self):
        super(LogNotifierTests, self).setUp()
        self.notifier = notifier.LogNotifier()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    def test_notify_about_instance(self, mock_log):
        instance = mock.Mock(uuid='fake-uuid')
        msg = "Preemptible instance %s was deleted."
        self.notifier.notify_about_instance(instance)
        mock_log.assert_called_once_with(msg, instance.uuid)

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action(self, mock_error, mock_info):
        action = fakes.make_reaper_action()
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, "
               "requested instances: %s, event: %s")
        mock_info.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower())
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_success(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.SUCCESS)
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, victims: %s")
        mock_info.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.victims)
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_fail(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.FAILED,
                                          fault_reason="Action failed")
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, fault reason: %s")
        mock_error.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_canceled(self, mock_error, mock_info):
        action = fakes.make_reaper_action(state=ra.ActionState.CANCELED,
                                          fault_reason="Action canceled")
        self.notifier.notify_about_action(action)
        msg = ("Reaper request %s, state: %s, requested instances: %s,"
               " event: %s, fault reason: %s")
        mock_error.assert_called_once_with(
            msg, action.uuid, action.state.value.lower(),
            action.requested_instances, action.event.value.lower(),
            action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION)
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s"
        mock_info.assert_called_once_with(msg, action.uuid,
                                          action.state.value.lower())
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_succ(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.SUCCESS)
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, victims: %s"
        mock_info.assert_called_once_with(msg, action.uuid,
                                          action.state.value.lower(),
                                          action.victims)
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_fail(self, mock_error, mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.FAILED, fault_reason="Action failed")
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, fault reason: %s"
        mock_error.assert_called_once_with(msg, action.uuid,
                                           action.state.value.lower(),
                                           action.fault_reason)
        mock_info.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.info')
    @mock.patch('aardvark.reaper.notifier.log_notifier.LOG.error')
    def test_notify_about_action_state_calc_canceled(self, mock_error,
                                                     mock_info):
        action = fakes.make_reaper_action(
            event=ra.ActionEvent.STATE_CALCULATION,
            state=ra.ActionState.CANCELED, fault_reason="Action canceled")
        self.notifier.notify_about_action(action)
        msg = "State calculation %s, state: %s, fault reason: %s"
        mock_error.assert_called_once_with(msg, action.uuid,
                                           action.state.value.lower(),
                                           action.fault_reason)
        mock_info.assert_not_called()


class EmailNotifierTests(ReaperNotifierTests):

    notifier_name = "EmailNotifier"

    def setUp(self):
        super(EmailNotifierTests, self).setUp()
        self.notifier = notifier.EmailNotifier()
        CONF.reaper_notifier.sender = "no-reply@cern.ch"
        CONF.reaper_notifier.default_email_domain = '@cern.ch'
        CONF.reaper_notifier.smtp_password = None
        self.cc_addresses = ['cc1@cern.ch', 'cc2@cern.ch']
        self.bcc_addresses = ['bcc1@cern.ch', 'bcc2@cern.ch']
        CONF.reaper_notifier.cc = self.cc_addresses
        CONF.reaper_notifier.bcc = self.bcc_addresses

    def test_generate_message(self):
        instance = mock.Mock(owner='owner', uuid='fake_uuid',
                             user_id='fake_user')
        type(instance).name = mock.PropertyMock(return_value='fake_name')
        CONF.reaper_notifier.subject = 'instance <instance_uuid> killed'
        CONF.reaper_notifier.body = 'Hi <user_id>, <instance_name> was killed'
        message = self.notifier.generate_message(instance, self.cc_addresses)
        expected_subject = 'instance fake_uuid killed'
        expected_body = 'Hi fake_user, fake_name was killed'
        subject = email.header.decode_header(message['Subject'].encode())[0][0]
        # For Python3 subject now is byte buffer so make it a string
        subject = subject.decode('utf-8')
        message_body = base64.b64decode(
            message.get_payload()[0].get_payload()).decode('utf-8')
        self.assertEqual(expected_subject, subject)
        self.assertEqual(expected_body, message_body)
        self.assertEqual(CONF.reaper_notifier.sender, message['From'])
        self.assertEqual("%s@cern.ch" % instance.owner, message['To'])
        self.assertEqual(', '.join(CONF.reaper_notifier.cc), message['cc'])

    @mock.patch('smtplib.SMTP')
    def test_send_message_without_pass(self, mock_smtplib):
        mock_smtp_conn = mock.Mock()
        mock_smtplib.return_value = mock_smtp_conn
        recipients = ['recients']
        message = mock.Mock()
        self.notifier.send_message(recipients, message)
        mock_smtp_conn.ehlo.assert_not_called()
        mock_smtp_conn.starttls.assert_not_called()
        mock_smtp_conn.login.assert_not_called()
        mock_smtp_conn.sendmail.assert_called_once_with(
            from_addr=CONF.reaper_notifier.sender,
            to_addrs=recipients,
            msg=message.as_string()
        )

    @mock.patch('smtplib.SMTP')
    def test_send_message_with_pass(self, mock_smtplib):
        CONF.reaper_notifier.smtp_password = 'smtp_pass'
        mock_smtp_conn = mock.Mock()
        mock_smtplib.return_value = mock_smtp_conn
        recipients = ['recients']
        message = mock.Mock()
        self.notifier.send_message(recipients, message)
        self.assertEqual(2, mock_smtp_conn.ehlo.call_count)
        mock_smtp_conn.starttls.assert_called_once_with()
        mock_smtp_conn.login.assert_called_once_with(
            CONF.reaper_notifier.sender, CONF.reaper_notifier.smtp_password
        )
        mock_smtp_conn.sendmail.assert_called_once_with(
            from_addr=CONF.reaper_notifier.sender,
            to_addrs=recipients,
            msg=message.as_string()
        )

    @mock.patch('aardvark.reaper.notifier.EmailNotifier.generate_message')
    @mock.patch('aardvark.reaper.notifier.EmailNotifier.send_message')
    @mock.patch('aardvark.reaper.notifier.email_notifier.LOG.error')
    def test_notify_about_instance(self, mock_error, mock_send, mock_generate):
        instance = mock.Mock(owner='owner', uuid='fake_uuid',
                             user_id='fake_user')
        type(instance).name = mock.PropertyMock(return_value='fake_name')
        generated_message = mock.Mock()
        mock_generate.return_value = generated_message
        self.notifier.notify_about_instance(instance)
        mock_generate.assert_called_once_with(instance, self.cc_addresses)
        recipients = ["owner@cern.ch"] + self.cc_addresses + self.bcc_addresses
        mock_send.assert_called_once_with(recipients, generated_message)
        mock_error.assert_not_called()

    @mock.patch('aardvark.reaper.notifier.EmailNotifier.generate_message')
    @mock.patch('aardvark.reaper.notifier.EmailNotifier.send_message')
    @mock.patch('aardvark.reaper.notifier.email_notifier.LOG.error')
    def test_notify_about_instance_failed_to_send(self, mock_error, mock_send,
                                                  mock_generate):
        instance = mock.Mock(owner='owner', uuid='fake_uuid',
                             user_id='fake_user')
        type(instance).name = mock.PropertyMock(return_value='fake_name')
        generated_message = mock.Mock()
        mock_generate.return_value = generated_message
        exception = IOError("test")
        mock_send.side_effect = exception
        self.notifier.notify_about_instance(instance)
        mock_generate.assert_called_once_with(instance, self.cc_addresses)
        recipients = ["owner@cern.ch"] + self.cc_addresses + self.bcc_addresses
        mock_send.assert_called_once_with(recipients, generated_message)
        error_msg = ("Failed to send email message to %s regarding instance"
                     " %s because: %s")
        mock_error.assert_called_once_with(error_msg, "owner@cern.ch",
                                           instance.uuid, exception)
