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

''' Search Imgur for a random image '''

import ConfigParser
import datetime
import json
import logging
import random

import os
import requests
from hogar.Utils.StringUtils import ignore_case_replace
from hogar.static import values as static_values

logger = logging.getLogger(__name__)

api_base = 'https://api.imgur.com/3/'
search_api = 'https://api.imgur.com/3/gallery/search/top/?q={term}'
credits_api = 'https://api.imgur.com/3/credits'

def enabled():
    '''
        Enabled

        Is this plugin enabled. Returning false here
        will cause this plugin to be ignored by the
        framework entirely.

        --
        @return bool
    '''

    return True

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

    return ['img']

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

def _get_client_id():
    '''
        Get Client ID

        Get the configured Imgur Client-ID

        --
        @return str

    '''
    config = ConfigParser.ConfigParser()
    config.read(
        os.path.join(os.path.dirname(__file__), '../../../settings.ini'))

    return config.get('imgur', 'client_id', '')

def _allow_nsfw():
    '''
        Allow NSFW

        Check if the results may have nsfw
        entries

        --
        @return bool
    '''

    config = ConfigParser.ConfigParser()
    config.read(
        os.path.join(os.path.dirname(__file__), '../../../settings.ini'))

    return config.getboolean('imgur', 'nsfw')

def _client_id_set():
    '''
        Client ID Set

        Check if the Imgur ClientID has been set.

        --
        @return bool
    '''

    if len(_get_client_id()) > 0:
        return True

    return False

def _get_headers():
    '''
        Get Headers

        Get headers prepared for a request to the Imgur API

        @return dict
    '''
    return {
        'User-Agent': 'hogar v{version}'.format(
            version = static_values.version),
        'Authorization': 'Client-ID {client_id}'.format(
            client_id = _get_client_id())
    }

def _ask_imgur(url):
    '''
        Make an Api request to imgur, searching
        for a term.

        --
        @param url:str

        @return str

    '''
    try:

        response = requests.get(url,
                                headers = _get_headers(),
                                verify = static_values.verify_ssl)

        response = json.loads(response.text.strip())

    except Exception, e:

        return 'failed: {exception}'.format(exception = e)

    return response

def _get_random_image(term):
    '''
        Get Random Image

        Get a random image from Imgur

        --
        @param term:str

        @return str
    '''
    data = _ask_imgur(search_api.format(
        term = term.encode('utf-8')))

    if 'data' not in data or len(data['data']) <= 0:
        return 'Imgur query had no results'

    # Results from the search may contain image data
    # models or gallery data models. Filter the
    # choices we make by ones that are not albums
    is_album = True
    while is_album:

        # Try and filter out images that are marked as
        # nsfw if the config is set for that.
        if _allow_nsfw():
            image_data = random.choice(data['data'])
        else:
            nsfw = True
            while nsfw:
                image_data = random.choice(data['data'])
                if not image_data['nsfw']:
                    nsfw = False

        if not image_data['is_album']:
            is_album = False

    response = ("\nTitle: {title}\n"
                "Link: {link}")

    return response.format(
        title = image_data['title'], link = image_data['link'])

def _get_credits():
    '''
        Get Credits

        Ask Imgur how many request credits are left

        --
        @return str
    '''
    data = _ask_imgur(credits_api)

    response = ("\nRemaining Requests: {remaining}\n"
                "Request Reset At: {reset_at}")

    return response.format(
        remaining = data['data']['ClientRemaining'],
        reset_at = datetime.datetime.fromtimestamp(
            int(data['data']['UserReset'])).strftime('%Y-%m-%d %H:%M:%S'))

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

    if not _client_id_set():
        return ('Imgur Client-ID not set. Get one at '
                'https://api.imgur.com/oauth2/addclient')

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

    # Remove the trigger command
    for command in commands():
        text = ignore_case_replace(command, '', text).strip()

    if text == 'credits':
        response = _get_credits()
    else:
        response = _get_random_image(text)

    return response
