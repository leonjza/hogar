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

__author__ = 'Leon Jacobs'

import os
import sys
import logging
import ConfigParser
import time
import requests
import urllib
import json
import traceback
import time
import multiprocessing as mp
from datetime import datetime

from hogar.static import values as static_values
from hogar.Utils.DBUtils import DB
from hogar.Models.Base import db

from hogar.Utils import PluginLoader
from hogar.Utils import Scheduler
from hogar import ResponseHandler

# read the required configuration
config = ConfigParser.ConfigParser()
config.read('settings.ini')

# set up logging to file
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    filename = os.path.dirname(os.path.realpath(__file__)) + '/var/hogar.log',
    filemode = 'a'
)
logger = logging.getLogger(__name__)

# make some sub modules stfu
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('peewee').setLevel(logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

# plugin storage
command_map = {}

def banner():

    '''
        Print the Hogar Banner

        --
        @return None
    '''

    print '''
.__
|  |__   ____   _________ _______
|  |  \ /  _ \ / ___\__  \\\\_  __ \\
|   Y  (  <_> ) /_/  > __ \|  | \/
|___|  /\____/\___  (____  /__|
     \/      /_____/     \/
                   v{v} - @leonjza
    '''.format(v = static_values.version)
    return

def wait(t = 60):

    '''
        Wait

        Causes a 'sleep' / lock state for t amount
        of seconds

        --
        @return None
    '''

    time.sleep(t)

    return

def response_handler(response):

    '''
        Response Handler

        Mediates an async task hadoff to the plugin manager.
        This function relies on the global command_map
        to know which plugins are available for use.

        --
        @param  response:dict   The parsed Telegram response object.

        @return None
    '''

    try:

        logger.debug('Starting response_handler for update ID {id}'.format(
            id = response['update_id'])
        )

        handle = ResponseHandler.Response(response, command_map)

        # Check if the ACL system is enabled and or if
        # the user is allowed to send this bot messages
        if handle.check_acl():
            handle.run_plugins()

    except Exception, e:
        traceback.print_exc()
        raise e

    return

def main():

    '''
        The start of Hogar

        This is the main entry point for Hogar. An infinite loop
        is started to handle the long poll to the Telegram API.
        Timeouts to the poll endpoint are considered ok and
        a new connection will be made.

        Updates received from the endpoint will spawn async
        update tasks for further processing, allowing for
        a new long poll to happen.

        --
        @return None
    '''

    logger.debug('Setting up env for the long poller')

    LONG_POLL_TIME = config.getint('advanced', 'long_poll_time')
    API_TOKEN = config.get('main', 'bot_access_token', '')
    LAST_REQUEST_ID = 0
    NOW = int(datetime.now().strftime('%s'))
    LAST_POLL_START = NOW

    logger.info('Longpoll time is: {long_poll_time}'.format(
        long_poll_time = LONG_POLL_TIME))

    # Check that we know the bot access token
    if len(API_TOKEN) < 1:
        raise ValeError('Please define a Bot Access token in the settings file.')

    while True:

        NOW = int(datetime.now().strftime('%s'))
        logger.debug(
            'New poller from request ID {request_id}. Previous poller time: {duration}s'.format(
                request_id = LAST_REQUEST_ID,
                duration = NOW - LAST_POLL_START
            )
        )
        LAST_POLL_START = NOW

        # We will watch for timeouts as that is kinda how the
        # whole long polling things works :)
        try:

            # Send the request
            response = requests.get(
                static_values.telegram_api_endpoint.format(
                    token = API_TOKEN,
                    method = 'getUpdates',
                    options = urllib.urlencode({
                        'offset': LAST_REQUEST_ID,
                        'limit': 100,
                        'timeout': LONG_POLL_TIME
                    })
                ),
                timeout = LONG_POLL_TIME,
                headers = static_values.headers
            )

            logger.debug('Request was made to url: {url}'.format(
                url = response.url).replace(API_TOKEN, '[api-key-redact]'))

        except requests.exceptions.Timeout, e:

            # The long poll should just be refreshed
            logger.debug('Request timed out: {error}'.format(error = str(e)))
            continue

        # Check that the request was actually successful
        if not response.status_code == requests.codes.ok:

            # Ok. The response was not ok. We will log and wait
            # a little bit as the Telegram API may be grumpy
            logger.warning('Update check call failed. Server responded with HTTP code: {code}'.format(
                code = response.status_code
            ))

            # Wait a little for the dust to settle and
            # retry the update call
            wait()
            continue

        try:
            response_data = json.loads(response.text.strip())

        except ValueError, e:

            logger.error('Parsing response Json failed with: {err}'.format(err = str(e)))

            # Wait a little for the dust to settle and
            # retry the update call
            wait()
            continue

        # Ensure that the response from the Telegram API is ok
        if 'ok' not in response_data or not response_data['ok']:
            logger.error('Response from Telegram API was not OK. We got: {resp}'.format(
                resp = str(response_data)
            ))
            continue

        # Check that some data was received from the API
        if not response_data['result']:
            logger.debug('This poll retreived no data')
            continue

        # Update the last known maximum request ID. This is used
        # in the next long poll so that we only receive new
        # messages
        max_request_id = max([x['update_id'] for x in response_data['result']])
        LAST_REQUEST_ID =  max_request_id + 1 if ((max_request_id + 1) >= LAST_REQUEST_ID) else LAST_REQUEST_ID

        # Start a response handler for every message received
        # in the long poll. We make use of a pool that will
        # handle only a few requests at a time
        pool = mp.Pool(processes = 4)

        # Add every message to the pool
        for message in response_data['result']:
            pool.apply_async(response_handler, args=(message,))

        # Close and join the results.
        pool.close()
        pool.join()

    return

if __name__ == '__main__':

    '''
        Hogar entry point.

        Running Hogar with __name__ as '__main__' (i.e python start.py) will
        allow Hogar to bootstrap the plugin loading and kick off the main
        routine.

        Providing 'setupdb' as an argument will have Hogar run any datebase
        migrations that may be outstanding.
    '''

    banner()

    # prepare a db setup command
    if len(sys.argv) > 1 :
        if sys.argv[1] == 'setupdb':

            logger.debug('Preparing to do database setup')
            DB.setup()
            logger.info('Database succesfully setup')
            print ' * Setup of database `%s` complete' % db.database
            sys.exit(0)

        else:
            print ' * Supported arguments are: setupdb'
            sys.exit(0)

    print ' * Loading plugins...'
    command_map = PluginLoader.prepare_plugins()

    if not command_map:
        print ' * No plugins found. Aborting.'
        sys.exit(1)

    print ' * Loaded plugins for {number} message types: {commands}'.format(
        number = len(command_map.keys()),
        commands = '; '.join(command_map.keys())
    )

    print ' * Booting the scheduler'
    Scheduler.boot()

    print ' * Starting long poll to the Telegram API'
    main()
