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

''' A simple key, value storage / retreival plugin '''

from hogar.Models.Base import db
from hogar.Models.LearnKey import LearnKey
from hogar.Models.LearnValue import LearnValue
import peewee
import logging
logger = logging.getLogger(__name__)

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

        --
        @return list
    '''

    return ['learn', 'forget', 'show']

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

def _learn(text):

    '''
        Learn

        Takes text, splits it on the first 'as' word and treats
        the 2 strings as k, v for storage.

        --
        @param  text:str    The message with the k, v pair

        @return string
    '''

    # k, v is split by the 'as' keyword
    request_key = text.split('as', 1)[0].strip()
    request_value = text.split('as', 1)[1].strip()

    # the key 'all' is reserved
    if request_key == 'all':
        return 'The key \'all\' is reserved. Please choose another'

    # Check if we don't already have this value
    try:
        values = LearnValue.select().join(LearnKey).where(LearnValue.value == request_value).get()

        # Return that we already know about this.
        return 'I already know about \'{value}\'. Checkout \'/show {key}\''.format(
            value = request_value,
            key = values.name.name
        )

    except LearnValue.DoesNotExist, e:
        pass

    # Get or create the key if it does not already exist
    try:
        key = LearnKey.create(name = request_key)

    except peewee.IntegrityError:
        key = LearnKey.get(LearnKey.name == request_key)

    # Prepare the value, and save it with the key
    stored_value = LearnValue.create(
        name = key, value = request_value
    )

    return 'Ok, learnt that {k} is :{v}'.format(
        k = request_key, v = request_value
    )

def _forget(text):

    '''
        Forget

        Takes the text argument and attempts to delete
        any known references to it.

        --
        @param  text:str    The key

        @return string
    '''

    # Check if we don't already have this value
    try:
        key = LearnKey.get(LearnKey.name == text)
        key.delete_instance(recursive=True)

        return 'Ok, I have forgotten everything I know about \'{k}\''.format(k = text)

    except LearnKey.DoesNotExist, e:
        pass

    return 'I dont know anything about {k}'.format(k = text)

def _show(text):

    '''
        Learn

        Takes the text argument and attempts to show
        any known references to it.

        --
        @param  text:str    The key

        @return string
    '''

    # Check if we should show all the keys
    # that we know of
    if text == 'all':

        if (LearnKey.select().count()) <= 0:
            return 'I currently don\'t know anything.'

        response = ' I currently know about:\n\n'

        for k in LearnKey.select():
            response += '(#{id}) {key}\n'.format(
                id = k.id,
                key = k.name)

        return response

    # Check if we have this value
    values = [v.value for v in LearnValue.select().join(LearnKey).where(LearnKey.name == text)]

    if len(values) > 0:

        return '\'{k}\' is: {v}'.format(
            k = text,
            v = ', '.join(values)
        )

    return 'I have no idea what you are talking about.'

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

    # Remove the trigger command
    for command in commands():
        text = text.replace(command, '', 1).strip()

    # Map actions to function and () them
    do_action = {
        'learn' : _learn,
        'forget': _forget,
        'show'  : _show
    }
    response = do_action[action](text)

    return response
