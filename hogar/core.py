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
import atexit
import logging
import ConfigParser
import time
import requests
import urllib
import json
import traceback
import time
import atexit
import multiprocessing as mp
from datetime import datetime

from hogar.static import values as static_values
from hogar.Utils import Scheduler
from hogar.Utils import Daemon
from hogar import ResponseHandler

# read the required configuration
config = ConfigParser.ConfigParser()
config.read('settings.ini')

logger = logging.getLogger(__name__)

def pickle_response_handler(response, command_map):

    '''
        Pickle Response Handler

        A small helper function that calls the App
        class' response_handler method. This is needed
        so that the async_task has something that is
        in a picklable state -_-

        --
        @param  response:dict       The parsed Telegram response object.
        @param  command_map:dict    The parsed commands available.

        @return None
    '''

    App.response_handler(response, command_map)

    return

class App(Daemon.Daemon):

    '''
        The Hogar App Class

        This class extends the Utils.Daemon module to
        allow for hogar to be run in the background
        as a daemon
    '''

    # Parsed plugins are mapped here
    command_map = None

    def set_command_map(self, command_map):

        '''
            Set Command Map

            Mutator method to set this Objects
            command_map variable

            --
            @param  command_map:dict    An initiated command map

            @return None
        '''

        self.command_map = command_map

        return

    def wait(self, t = 60):

        '''
            Wait

            Causes a 'sleep' / lock state for t amount
            of seconds

            --
            @return None
        '''

        logger.warning('Waiting for {time} seconds'.format(
            time = t))

        time.sleep(t)

        return

    @staticmethod
    def response_handler(response, command_map):

        '''
            Response Handler

            Mediates an async task hadoff to the plugin manager.
            This function relies on the global command_map
            to know which plugins are available for use.

            --
            @param  response:dict       The parsed Telegram response object.
            @param  command_map:dict    The parsed commands available.

            @return None
        '''

        try:

            logger.debug('Starting response_handler for update ID {id}'.format(
                id = response['update_id']))

            handle = ResponseHandler.Response(response, command_map)

            # Check if the ACL system is enabled and or if
            # the user is allowed to send this bot messages
            if handle.check_acl():

                handle.run_plugins()

        except Exception, e:

            traceback.print_exc()
            raise e

        return

    def run(self):

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

        long_poll_time = config.getint('advanced', 'long_poll_time')
        api_token = config.get('main', 'bot_access_token', '')
        last_request_id = 0
        now = int(datetime.now().strftime('%s'))
        last_poll_start = now

        logger.info('Longpoll time is: {long_poll_time}'.format(
            long_poll_time = long_poll_time))

        # Check that we know the bot access token
        if len(api_token) < 1:
            raise ValeError('Please define a Bot Access token in the settings file.')

        # Boot the scheduler.
        Scheduler.boot(os.getpid())

        # Start the main loop
        while True:

            now = int(datetime.now().strftime('%s'))
            logger.debug(
                'New poller from request ID {request_id}. Previous poller time: {duration}s'.format(
                    request_id = last_request_id,
                    duration = now - last_poll_start
                )
            )
            last_poll_start = now

            # We will watch for timeouts as that is kinda how the
            # whole long polling things works :)
            try:

                # Send the request
                response = requests.get(
                    static_values.telegram_api_endpoint.format(
                        token = api_token,
                        method = 'getUpdates',
                        options = urllib.urlencode({
                            'offset': last_request_id,
                            'limit': 100,
                            'timeout': long_poll_time
                        })
                    ),
                    timeout = long_poll_time,
                    headers = static_values.headers
                )

                logger.debug('Request was made to url: {url}'.format(
                    url = response.url).replace(api_token, '[api-key-redact]'))

            # Catch a timeout. This is the core of how the long
            # poll actually works.
            except requests.exceptions.Timeout, e:

                # The long poll should just be refreshed
                logger.debug('Request timed out: {error}'.format(error = str(e)))
                continue

            # Any connection related error, we can retry after
            # we have waited for dust to settle.
            except requests.exceptions.ConnectionError, e:

                print ' * Error! Connection to Telegram failed with: {error}'.format(
                    error = str(e))

                # Start the wait
                self.wait()
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
                self.wait()
                continue

            try:
                response_data = json.loads(response.text.strip())

            except ValueError, e:

                logger.error('Parsing response Json failed with: {err}'.format(err = str(e)))

                # Wait a little for the dust to settle and
                # retry the update call
                self.wait()
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
            last_request_id =  max_request_id + 1 \
                if ((max_request_id + 1) >= last_request_id) else last_request_id

            # Start a response handler for every message received
            # in the long poll. We make use of a pool that will
            # handle only a few requests at a time
            pool = mp.Pool(processes = 4)

            # Add every message to the pool
            for message in response_data['result']:

                # Pop a worker in the pool
                pool.apply_async(pickle_response_handler,
                    args=(message, self.command_map,))

            # Close and join the results.
            pool.close()
            pool.join()

        return
