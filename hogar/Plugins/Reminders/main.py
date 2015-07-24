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

from recurrent import RecurringEvent
import datetime
import time
import json

from hogar.Models.RemindOnce import RemindOnce
from hogar.Models.RemindRecurring import RemindRecurring

import logging
logger = logging.getLogger(__name__)

def applicable_types():

    '''
        Applicable Types

        Returns the type of messages this plugin is for.
        See: hogar.static.values

        --
        @return list
    '''

    return ['text']

def commands():

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

    return ['remind', 'reminder']

def should_reply():

    '''
        Should Reply

        Specifies wether a reply should be sent to the original
        sender of the message that triggered this plugin.

        --
        @return bool
    '''

    return True

def reply_type():

    '''
        Reply Type

        Specifies the type of reply that should be sent to the
        sender. This is an optional function. See hogar.static.values
        for available types.

        --
        @return str
    '''

    return 'text'

def _extract_parts(text):

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
    # [script init] [recipient /(show/stop)] [once/every] [time]: [message]

    parts = {

        'recipient': None,
        'action': 'set',
        'recurrence': 'once',
        'time': None,
        'parsed_time': None,
        'message': None,
        'error': False,
        'error_message' : None
    }

    # Check the action_recipient
    action_recipient = text.split(' ')[0].strip()

    # Ensure that the action is something we understand
    if action_recipient not in ['me', 'us', 'show', 'stop']:

        parts['error'] = True
        parts['error_message'] = 'Unknown command: {c}'.format(
            c = action_recipient
        )

        return parts

    # We are happy with the action. show and stop
    # actions dont care about the rest
    if action_recipient in ['show', 'stop']:

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

def _set_once_reminder(r, orig_message):

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

def _set_recurring_reminder(r, orig_message):

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
        message = r['message']
    )

    return

def run(message):

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

    # Remove the trigger commands
    for command in commands():
        text = text.replace(command, '', 1).strip()

    # Now, parse the reminder line
    parts = _extract_parts(text)

    # If there was an error with the message, show it
    if parts['error']:

        format_help = 'remind [recipient /(show/stop)] [once/every] [time]: [message]'
        error_message = 'Reminder not set. Error was: {e}.\n\nReminder format is: {f}'.format(
            e = parts['error_message'],
            f = format_help
        )

        return error_message

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
