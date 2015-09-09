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

''' An access control plugin '''

import os
import ConfigParser
import logging

logger = logging.getLogger(__name__)

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

    return ['contact']

def commands ():
    '''
        Commands

        In the case of text plugins, returns the commands
        that this plugin should trigger for. For other
        message types, a empty list should be returned.

        --
        @return list
    '''

    return []

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

    # Read the configuration as the plugin is run()
    config = ConfigParser.ConfigParser()
    config.read(
        os.path.join(os.path.dirname(__file__), '../../../settings.ini'))

    config_owners = config.get('acl', 'owners', '').split(',')
    config_users = config.get('acl', 'users', '').split(',')

    # If we dont have any users configured, set a empty
    # list
    if not any(config_users):
        config_users = []

    # If we don't have an owner configured, log it and respond.
    if len(config_owners) < 1:
        logger.error('ACL modification denied for {first_name}. No owners configured'.format(
            first_name = message['from']['first_name']
        ))
        return 'I will only allow the owner to do this.'

    # If the request came from someone that is not a owner, log and respond
    if str(message['from']['id']) not in config_owners:
        logger.error('ACL modification denied for {first_name}. Not an owner'.format(
            first_name = message['from']['first_name']
        ))
        return 'I will only allow the owner to do this.'

    # check if the received contact is considered a user
    if str(message['contact']['user_id']) in config_users:

        # Remove the user
        logger.info('{owner_first_name} removed {first_name} ({id}) as a user'.format(
            owner_first_name = message['from']['first_name'],
            first_name = message['contact']['first_name'],
            id = message['contact']['user_id']
        ))

        config_users.remove(str(message['contact']['user_id']))
        config.set('acl', 'users', ','.join(config_users))

        status = 'Removed {first_name} ({id}) as a user.'.format(
            first_name = message['contact']['first_name'],
            id = message['contact']['user_id']
        )

    else:

        # Add the user
        logger.info('{owner_first_name} added {first_name} ({id}) as a user'.format(
            owner_first_name = message['from']['first_name'],
            first_name = message['contact']['first_name'],
            id = message['contact']['user_id']
        ))

        config_users.append(str(message['contact']['user_id']))
        config.set('acl', 'users', ','.join(config_users))

        status = 'Added {first_name} ({id}) as a user.'.format(
            first_name = message['contact']['first_name'],
            id = message['contact']['user_id']
        )

    # Write the confuration changes
    with open(
            os.path.join(os.path.dirname(__file__), '../../../settings.ini'), 'wb') as s:
        config.write(s)

    return status
