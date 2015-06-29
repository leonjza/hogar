#!/usr/bin/env python

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

import requests
import urllib
import ConfigParser
from hogar.static import values as static_values

import logging
logger = logging.getLogger(__name__)

config = ConfigParser.ConfigParser()
config.read('settings.ini')

API_TOKEN = config.get('main', 'bot_access_token', '')

def _nothing(recipient, message):

    '''
        Do Nothing(tm)

        --
        @param  recipient:dict  A dictionary of recipient information
        @param  message:str     The text to be sent

        @return None
    '''

    return

def _get_mention(recipient):

    '''
        Get a Mention

        Determine how to greet/identify the recipient of
        a message.

        --
        @param  recipient:dict  The dictionary containing recipient info

        @return str
    '''

    return '{u}: '.format(u = recipient['username']) \
        if recipient['username'] is not None \
        else '{f}: '.format(f = recipient['first_name'])

def _truncate_text(message, length = 1900):

    '''
        Truncate Text

        --
        @param  message:str The text to be truncated
        @param  length:int  The maximum length of the message.

        @return str
    '''

    return message[:length] + '[truncated]' if len(message) > length else message

def _send_text_message(recipient, message):

    '''
        Send a Text Telegram message.

        --
        @param  recipient:dict  A dictionary of recipient information
        @param  message:str     The text to be sent

        @return None
    '''

    # Send the request
    response = requests.get(
        static_values.telegram_api_endpoint.format(
            token = API_TOKEN,
            method = 'sendMessage',
            options = urllib.urlencode({
                'chat_id': recipient['id'],
                'text': _truncate_text(_get_mention(recipient) + message).encode('utf-8')
            })
        ),
        headers = static_values.headers
    )

    return

def send_message(recipient, message_type, message):

    '''
        Send a Telegram Message.

        This method takes the message_type argument
        and attempts to map it to the appropriate
        method that will handle the sending.

        --
        @param  recipient:dict      A dictionary of recipient information
        @param  message_type:str    The type of message to send
        @param  message:str         The message to be sent

        @return None
    '''

    options = {
        'text' : _send_text_message,
        'audio' : _nothing,
        'document' : _nothing,
        'photo' : _nothing,
        'sticker' : _nothing,
        'video' : _nothing,
        'contact' : _nothing,
        'location' : _nothing,
    }

    # Log the sending of a message
    logging.info('Sending {message_type} message to {recipient}'.format(
        message_type = message_type,
        recipient = recipient['first_name']
    ))

    # Run the appropriate function
    options[message_type](recipient, message)

    return
