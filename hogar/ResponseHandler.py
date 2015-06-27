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

from hogar.static import values as static_values
from hogar.Utils import PluginLoader
from hogar.Utils import Telegram
import traceback

import logging
logger = logging.getLogger(__name__)

class Response(object):

    '''
        The Hogar Response handler.

        This class mediates the connection between actual
        messages received by the API and the plugins
        that are available for them.
    '''

    response = None
    command_map = None
    message_type = None
    plugins = None
    sender_information = {'id' : None, 'first_name' : None, 'last_name' : None, 'username' : None }

    def __init__(self, response, command_map):

        '''
            Prepare a new Response() instance.

            This __init__ will do a lot of the heavy lifting
            when it comes to determining the message_type,
            and which plugins are available for it.

            --
            @param  response:dict       The parsed Telegram response.
            @param  command_map:dict    The command/type/plugin map.

            @return None
        '''

        if not response['message']:
            raise ValueError('No message payload in the response? WTF?')

        self.response = response['message']
        self.command_map = command_map

        self.message_type = self._get_message_type()
        self.sender_information = self._get_sender_information()
        self.plugins = self._find_applicable_plugins()

        return

    def _get_message_type(self):

        '''
            Get the message type.

            --
            @return str
        '''

        # Search for the message type
        type_search = [message_type for message_type in static_values.possible_message_types \
            if message_type in self.response]

        # check that we only got 1 result back from the search
        if len(type_search) > 1:
            logger.warning('More than 1 message type found: ({res}). Selecting only the first entry'.format(
                res = ', '.join(type_search)
            ))

        return type_search[0]

    def _get_sender_information(self):

        '''
            Get information about who sent a message.

            --
            @return dict
        '''

        sender = self.response

        sender_information = {
            'id' : self.response['chat']['id'],
            'first_name' : self.response['from']['first_name'],
            'last_name' : self.response['from']['last_name'],
            'username' : '@{u}'.format(u = self.response['from']['username']) \
                if 'username' in self.response['from'] else None
        }

        return sender_information

    def _find_applicable_plugins(self):

        '''
            Find Applicable plugins based on message type.

            --
            @return dict
        '''

        # Text types are special for the fact that they can have
        # command triggers too. We will only return a map
        # of those that have the command.
        #
        # We will have to clean up the text and remove any '/' or
        # '@' mentions so that the command may be triggered
        if self.message_type == 'text':

            text = self.response['text']

            # Remove a mention. This could be the case
            # if the bot was mentioned in a chat room
            if text.startswith('@'):
                text = text.split(' ', 1)[1].strip()

            # Some bots will accept commands that started
            # with a '/'
            if text.startswith('/'):
                text = text.replace('/', '', 1).strip()

            return [x for x in self.command_map['text'] if text.split(' ')[0] in x['commands']]

        return self.command_map[self.message_type]

    def run_plugins(self):

        '''
            Run Plugins

            This is the main function responsible for executing
            the plugins that have been identified for this
            message.

            --
            @return None
        '''

        #TODO: Handle if no plugins are applicable!
        for plugin in self.plugins:

            try:

                logger.info('Running plugin: {plugin}'.format(plugin = plugin['name']))

                # Run the plugins run() method
                plugin_output = plugin['plugin'].run(self.response)

            except Exception, e:

                logger.error('Plugin {plugin} failed with: {error}: {trace}'.format(
                    plugin = plugin['name'],
                    error = str(e),
                    trace = traceback.print_exc()
                ))
                continue

            # If we should be replying to the message,
            # do it.
            if (plugin['plugin'].should_reply()):
                Telegram.send_message(self.sender_information, self.message_type, plugin_output)

        return
