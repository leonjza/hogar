# The MIT License (MIT)
#
# Copyright (c) 2015 Leon Jacobs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

''' A Simple Reminder Plugin '''
from hogar.Utils.StringUtils import ignore_case_replace
from recurrent import RecurringEvent
from dateutil.rrule import rrulestr
from hogar.Models.RemindOnce import RemindOnce
from hogar.Models.RemindRecurring import RemindRecurring
import os
import arrow
import datetime
import json
import ConfigParser
import logging

logger = logging.getLogger(__name__)

config = ConfigParser.ConfigParser()
config.read(
    os.path.join(os.path.dirname(__file__), '../../../settings.ini'))

def enabled ():
    '''
        Enabled

        Is this plugin enabled. Returning false here
        will cause this plugin to be ignored by the
        framework entirely.

        --
        @return bool
    '''

    return True

def applicable_types ():
    '''
        Applicable Types

        Returns the type of messages this plugin is for.
        See: hogar.static.values

        --
        @return list
    '''

    return ['text']

def commands ():
    '''
        Commands

        In the case of text plugins, returns the commands
        that this plugin should trigger for. For other
        message types, a empty list should be returned.

        If your plugin applies to any command (in the
        case of text messages), simply supply the a
        wildcard in the list ie. ['*']

        --
        @return list
    '''

    return ['reminder', 'remind']

def should_reply ():
    '''
        Should Reply

        Specifies wether a reply should be sent to the original
        sender of the message that triggered this plugin.

        --
        @return bool
    '''

    return True

def reply_type ():
    '''
        Reply Type

        Specifies the type of reply that should be sent to the
        sender. This is an optional function. See hogar.static.values
        for available types.

        --
        @return str
    '''

    return 'text'

def _extract_parts (text):
    '''
        Extract Parts

        Extract and parse the message, returning a dictionary
        describing the actions that should be taken

        --
        @param  text:string    The message sent by the user

        @return dict
    '''

    # Examples:
    # remind me once monday at 4pm, Help!
    # remind me once two weeks from now, Help!
    #
    # remind me every 5 minutes, Help!
    # remind me every 1 day, Help!
    #
    # remind show
    # remind stop #1

    # With the above examples, we can say that the
    # format should follow the following:
    #
    # [script init] [set / show /stop / help] [once/every] [time]: [message]

    parts = {

        'recipient': None,
        'action': 'set',
        'recurrence': 'once',
        'time': None,
        'parsed_time': None,
        'message': None,
        'error': False,
        'error_message': None
    }

    # Check the action_recipient
    action_recipient = text.split(' ')[0].strip()

    # Ensure that the action is something we understand
    if action_recipient not in ['set', 'show', 'stop', 'help']:
        parts['error'] = True
        parts['error_message'] = 'Unknown command: {c}'.format(
            c = action_recipient
        )

        return parts

    # We are happy with the action. show and stop
    # actions dont care about the rest
    if action_recipient in ['show', 'stop', 'help']:
        parts['action'] = action_recipient
        return parts

    # Set the recipient and remove it from the text
    text = text.replace(action_recipient, '', 1).strip()
    parts['recipient'] = action_recipient

    # Next part is to check the recurrence.
    recurrence = text.split(' ')[0].strip()

    # Check that the recurrence is valid
    if recurrence not in ['once', 'every']:
        parts['error'] = True
        parts['error_message'] = 'Unknown recurrence: {r}'.format(
            r = recurrence
        )

        return parts

    # Set the recurrence and remove it from the text
    # only of it is set to 'once'
    text = text.replace('once', '', 1).strip()
    parts['recurrence'] = recurrence

    # Next, we parse the time. For this we should be
    # able to split by ,
    if len(text.split(',', 1)) != 2:
        parts['error'] = True
        parts['error_message'] = 'Time and message should be seperated by a comma ( , ) character'

        return parts

    # Set the time and the message
    time = text.split(',', 1)[0].strip()
    message = text.split(',', 1)[1].strip()

    # Resolve the human time to something we can work
    # with
    r = RecurringEvent()
    parsed_time = r.parse(time)

    # If the time parsing failed, oh well.
    if parsed_time is None:
        parts['error'] = True
        parts['error_message'] = 'Unable to parse time: {t}'.format(
            t = time
        )

        return parts

    # Set the time and parsed time, as well as the message
    # that should be used
    parts['time'] = time
    parts['parsed_time'] = parsed_time
    parts['message'] = message

    return parts

def _set_once_reminder (r, orig_message):
    '''
        Set Once Reminder

        Record a reminder in the database to be sent.

        --
        @param  r:dict              The parsed message from the user
        @param  orig_message:str    The original message received

        @return str
    '''

    logger.debug('Storing reminder for {id}'.format(
        id = orig_message['chat']['id']
    ))

    RemindOnce.create(
        orig_message = json.dumps(orig_message),
        time = r['parsed_time'],
        message = r['message']
    )

    return

def _set_recurring_reminder (r, orig_message):
    '''
        Set Recurring Reminder

        Record a recurring reminder in the database to be sent.

        #TODO: Implement this

        --
        @param  r:dict              The parsed message from the user
        @param  orig_message:str    The original message received

        @return str
    '''

    logger.debug('Storing reminder for {id}'.format(
        id = orig_message['chat']['id']
    ))

    RemindRecurring.create(
        orig_message = json.dumps(orig_message),
        rrules = r['parsed_time'],
        next_run = rrulestr(r['parsed_time'],
                            dtstart = datetime.datetime.now()).after(datetime.datetime.now()),
        message = r['message']
    )

    return

def _show_all_reminders (message):
    '''
        Show All Reminders

        Returns all of the reminders for the appropriate
        chat ID that the message came from

        --
        @param  message:dict    The message sent by the user

        @return str
    '''

    response = '\n# One time reminders:\n\n'

    for reminder in RemindOnce.select().where(RemindOnce.sent == 0,
                                              RemindOnce.time >= datetime.datetime.now()):

        orig_message = json.loads(reminder.orig_message)
        if orig_message['chat']['id'] == message['chat']['id']:
            response += '(#{id}) {human} @{time} | {message}\n'.format(
                id = reminder.id,
                human = arrow.get(reminder.time,
                                  config.get('reminder', 'timezone', 'UTC')).humanize(),
                time = str(reminder.time),
                message = reminder.message[:20] + '...' \
                    if len(reminder.message) > 20 else reminder.message)

    response += '\n# Recurring reminders:\n\n'

    for reminder in RemindRecurring.select().where(RemindRecurring.sent == 0,
                                                   RemindRecurring.next_run >= datetime.datetime.now()):

        orig_message = json.loads(reminder.orig_message)
        if orig_message['chat']['id'] == message['chat']['id']:
            response += '(#{id}) {human} @{next_run} | {message}\n'.format(
                id = reminder.id,
                human = arrow.get(reminder.next_run,
                                  config.get('reminder', 'timezone', 'UTC')).humanize(),
                next_run = str(reminder.next_run),
                message = reminder.message[:20] + '...' \
                    if len(reminder.message) > 20 else reminder.message)

    return response

def _stop_reminder (message):
    '''
        Stop A Reminder

        Sets a reminder as sent so that it will not run
        again. This function also ensures that the
        reminder's chatID matches the chatID of
        the user requesting the stop

        --
        @param  message:dict    The message sent by the user

        @return str
    '''

    # Remove the command form the text
    text = message['text'].replace('remind stop', '').strip()

    # Split the remainder of the text into 2 parts.
    # We are expecting either 'once' or 'recurring'
    # as the type of reminder and a number
    parts_list = text.split(' ')

    # Check the length of the list and assume a typo
    # if its not 2
    if len(parts_list) != 2:
        return 'Could not understand what you wanted. Expecting:\n' + \
               'remind stop [once/recurring] [message number]'

    message_type = parts_list[0]
    message_number = parts_list[1]

    # Check that we got once or recurring
    if message_type not in ['once', 'recurring']:
        return 'Could not figure out which message type you are referring to. ' + \
               'Expected \'once\' / \'recurring\''

    # For once time messages, perform the chatID check
    # and mark the message as sent if its ok
    if message_type == 'once':

        try:
            m = RemindOnce.select().where(RemindOnce.id == message_number).get()

            if json.loads(m.orig_message)['chat']['id'] == message['chat']['id']:

                m.sent = 1
                m.save()

            else:

                logger.warning('User {id} tried to disable a reminder they dont own'.format(
                    id = message['chat']['id']))
                return 'That message number does not exist or you dont own it.'

        except RemindOnce.DoesNotExist:
            return 'That message number does not exist or you dont own it.'

        return 'Done stopping the one time reminder'

    # The same here for the recurring message.
    if message_type == 'recurring':

        try:
            m = RemindRecurring.select().where(RemindRecurring.id == message_number).get()

            if json.loads(m.orig_message)['chat']['id'] == message['chat']['id']:

                m.sent = 1
                m.save()

            else:

                logger.warning('User {id} tried to disable a reminder they dont own'.format(
                    id = message['chat']['id']))
                return 'That message number does not exist or you dont own it.'

        except RemindRecurring.DoesNotExist:
            return 'That message number does not exist or you dont own it.'

        return 'Done stopping the recurring reminder'

    # We will most probably never get here, but
    # just in case...
    return 'Nothing happend...'

def _show_help (message):
    '''
        Show Help

        Shows usage help

        --

        @return None
    '''

    h = '\n# Reminder Plugin Help:\n'
    h += 'Commands Sytax:\n'
    h += 'remind [ set / show / stop / help ] [once/every] [time], [message]\n\n'
    h += 'Descriptions:\n'
    h += ' - set    : set a reminder for the current chat\n'
    h += ' - show   : show all reminders\n'
    h += ' - stop   : stop a reminder\n'
    h += ' - help   : show this help\n'

    return h

def run (message):
    '''
        Run

        Run the custom plugin specific code. A returned
        string is the message that will be sent back
        to the user.

        --
        @param  message:dict    The message sent by the user

        @return str
    '''

    # Get the message contents
    text = message['text']

    # Remove a mention. This could be the case
    # if the bot was mentioned in a chat room
    if text.startswith('@'):
        text = text.split(' ', 1)[1].strip()

    # Some bots will accept commands that started
    # with a '/'
    if text.startswith('/'):
        text = text.replace('/', '', 1).strip()

    # Try and determine what was the trigger command
    # for this plugin.
    action = text.split(' ')[0].strip()

    # Hopefully we never get here, but just in case.
    if action not in commands():
        return 'Sorry, I don\'t know what to do with: {command}'.format(
            command = action
        )

    # Remove the trigger command
    for command in commands():
        text = ignore_case_replace(command, '', text).strip()

    # Now, parse the reminder line
    parts = _extract_parts(text)

    # If there was an error with the message, show it
    if parts['error']:
        error_message = 'Reminder not set. Error was: {e}.\n\n{help}'.format(
            e = parts['error_message'],
            help = _show_help(None)
        )

        return error_message

    # Handle a few control commands that should show
    # stop or display help for this plugin
    if parts['action'] in ['show', 'stop', 'help']:
        handle_action = {
            'show': _show_all_reminders,
            'stop': _stop_reminder,
            'help': _show_help,
        }

        # Handle and return the returned message
        return handle_action[parts['action']](message)

    # Fake a small case-like statement for the once or
    # every message types
    handle_recurrence_types = {
        'once': _set_once_reminder,
        'every': _set_recurring_reminder
    }

    # Run the appropriate set function
    handle_recurrence_types[parts['recurrence']](parts, message)

    # Respond with the fact that the reminder is set.
    response = 'Reminder set for: {t} with message: {m}'.format(
        t = parts['parsed_time'],
        m = parts['message']
    )

    return response
