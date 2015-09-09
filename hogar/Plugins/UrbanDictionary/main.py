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

''' A simple Urban Dictionary Lookup Plugin '''

from hogar.Utils.StringUtils import ignore_case_replace
import requests
import json
import logging

logger = logging.getLogger(__name__)
api = 'http://api.urbandictionary.com/v0/define?term={term}'

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

    return ['urban', 'whatis']

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

    # Get the text
    text = message['text']

    # Remove the trigger command
    for command in commands():
        text = ignore_case_replace(command, '', text).strip()

    # Call Urban Dictionary API for a definition
    # if the user supplied term
    try:

        logger.debug('Asking Urban Dictionary what is {term}'.format(
            term = text))

        # The actual lookup request
        response = requests.get(
            api.format(
                term = text.encode('utf-8')))

    except Exception, e:

        logger.error('Urban Dictionay lookup failed with: {error}'.format(
            error = str(e)))

        return 'Sorry, Urban Dictionary lookup failed'

    # Ensure the response was OK from an HTTP perspective
    if not response.status_code == requests.codes.ok:
        return 'Failed to ask Urban Dictionary what {term} means'.format(
            term = text)

    # Try and parse the response json
    try:
        response_data = json.loads(response.text.strip())

    except ValueError, e:

        logger.error('Parsing response Json failed with: {err}'.format(err = str(e)))

        # Wait a little for the dust to settle and
        # retry the update call
        return 'Failed to parse the Urban Dictionary response'

    # Try and parse a JSON response from the API
    try:

        # check that we actually got something
        if response_data['result_type'] == 'no_results':
            return 'The lookup returned no results.'

    except Exception, e:

        logger.error('Failed to extract definition and example with error: {error}'.format(
            error = str(e)))

        return 'Unable to parse response. See logs for more details.'

    # Get the actual definitions
    try:

        definition = response_data['list'][0]['definition']
        example = response_data['list'][0]['example']
        author = response_data['list'][0]['author']
        permalink = response_data['list'][0]['permalink']
        tags = ', '.join(response_data['tags'])

    except Exception, e:

        logger.error('Failed to extract definition and example with error: {error}'.format(
            error = str(e)))

        return 'Unable to parse response. See logs for more details.'

    # Construct the final response message
    final_definition = u'\'{term}\' is defined by \'{author}\' as:\n\n* Definition: {definition}\n* Example: {' \
                       u'example}\n\nTags: {tags}\n\nSee: {permalink}'.format(
        term = text,
        author = author,
        definition = definition,
        example = example,
        tags = tags,
        permalink = permalink)

    return final_definition
