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

''' Send a random Joke '''

import pyjokes
from hogar.Utils.StringUtils import ignore_case_replace

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

    return ['joke']

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

def _show_help ():
    '''
        Show Help

        Shows usage help

        --

        @return None
    '''

    h = '\n# Joke Plugin Help:\n'
    h += 'Commands Sytax:\n'
    h += 'joke <category>\n\n'
    h += 'Example:\n'
    h += ' joke neutral\n\n'
    h += 'Categories:\n'
    h += ' neutral, explicit, chuck, all'

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
            command = action)

    # Remove the trigger command
    for command in commands():
        text = ignore_case_replace(command, '', text).strip()

    if text == 'help':
        return _show_help()

    if text in ['neutral', 'explicit', 'chuck', 'all']:
        return pyjokes.get_joke(language = 'en', category = text)

    # Default to a neutral joke
    return pyjokes.get_joke(language = 'en', category = 'all')

