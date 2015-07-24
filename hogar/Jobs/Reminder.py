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

import traceback
import json
from datetime import datetime
from dateutil.rrule import rrulestr

from hogar.Utils import Telegram
from hogar.Models.RemindOnce import RemindOnce
from hogar.Models.RemindRecurring import RemindRecurring

import logging
logger = logging.getLogger(__name__)

def _get_sender_information(message):

    '''
        Get information about who sent a message.

        #TODO:
        #Copied from ResponseHandler. Move to a util

        --
        @return dict
    '''

    # Parse the Json in the database
    message = json.loads(message)

    sender_information = {

        'id' : message['chat']['id'],
        'first_name' : message['from']['first_name'],
        'last_name' : message['from']['last_name'] \
            if 'last_name' in message['from'] else None,
        'username' : '@{u}'.format(u = message['from']['username']) \
            if 'username' in message['from'] else None
    }

    return sender_information

def run_remind_once():

    '''
        Run Remind Once

        Find and send all of the once time reminders that are due

        --
        @return void
    '''

    logger.debug('Running Remind Once Job')

    try:

        for reminder in RemindOnce.select().where(RemindOnce.sent == 0, \
            RemindOnce.time <= datetime.now()):

            logger.debug('Sending one time reminder message with id {id}'.format(
                id = reminder.id
            ))

            # Send the actual reminder
            Telegram.send_message(
                _get_sender_information(reminder.orig_message),
                'text',
                reminder.message
            )

            # Mark it as complete
            reminder.sent = 1
            reminder.save()

    except Exception, e:

        print traceback.format_exc()

    return

def run_remind_recurring():

    '''
        Run Remind Recurring

        Find and send all of the recurring reminders that are due

        --
        @return void
    '''

    logger.debug('Running Remind Recurring')

    try:

        # Get reminders have have not been marked as completed, as well as
        # have their next_run date ready or not set
        for reminder in RemindRecurring.select().where(RemindRecurring.sent == 0, \
            ((RemindRecurring.next_run <= datetime.now()) | (RemindRecurring.next_run >> None))):

            # If we know the next_run date, send the message. If
            # we dont know the next_run, this will be skipped
            # and only the next_run determined
            if reminder.next_run is not None:

                logger.debug('Sending recurring reminder message with id {id}'.format(
                    id = reminder.id
                ))

                # Send the actual reminder
                Telegram.send_message(
                    _get_sender_information(reminder.orig_message),
                    'text',
                    reminder.message)

            # Lets parse the rrules and update the next_run time for
            # a message. We will use python-dateutil to help with
            # determinig the next run based on the parsed RRULE
            # relative from now.
            next_run = rrulestr(reminder.rrules,
                dtstart = datetime.now()).after(datetime.now())

            # If there is no next run, consider the
            # schedule complete and mark it as
            # sent
            if not next_run:

                reminder.sent = 1
                reminder.save()

            # Save the next run
            reminder.next_run = next_run
            reminder.save()

    except Exception, e:

        print traceback.format_exc()

    return