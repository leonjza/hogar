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

''' A descrition of your plugin '''
import random
import uuid
from hogar.Utils.StringUtils import ignore_case_replace, get_url_extention
from hogar.static import values as static_values
import requests
import json
import logging

logger = logging.getLogger(__name__)
api = 'http://ajax.googleapis.com/ajax/services/search/images?v=1.0&rsz=8&q={term}&imgsz=small|medium|large'

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

    return ['img']

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

    return 'photo'

def ask_google (term):
    '''
        Calls the Google API in serach of image URL's that relate
        to the Term

        --
        :param term: str    The term to search for
        :return:dict
    '''
    return_data = {
        'failed': False,
        'urls': []
    }

    # Call the Google API searching for images
    try:

        logger.debug('Asking Google Images for {term}'.format(
            term = term))

        # The actual lookup request
        response = requests.get(
            api.format(
                term = term.encode('utf-8')))

        response = json.loads(response.text.strip())

    except Exception, e:

        logger.error('Google Images lookup failed with: {error}'.format(
            error = str(e)))

        return_data['failed'] = True
        return return_data

    # Loop the response, populating the URLs to images
    for url in response["responseData"]["results"]:
        return_data['urls'].append({
            'url': url['url'],
            'title': url['titleNoFormatting']})

    return return_data

def save_image (info):
    '''
        Save Image

        Downloads and saves an image from a URL to the data
        directory

        --
        :param info:dict
        :return:str
    '''

    return_data = {
        'location': static_values.data_dir + '/no_image.png',
        'caption': 'Failed to download the selected image.'
    }

    # We need to determine a file name where the image should
    # be stored to send later. Lets get the extention first
    ext = get_url_extention(info['url'])

    if ext not in ['.jpg', '.png', '.gif', '.bmp']:
        return  return_data

    file_name = static_values.data_dir + '/' + str(uuid.uuid4()) + ext
    logger.debug('Saving image from {url} to {filename}'.format(
        url = info['url'],
        filename = file_name
    ))

    try:
        with open(file_name, 'wb') as handle:
            image_stream = requests.get(info['url'], stream = True)

            if not image_stream.ok:
                return return_data

            for block in image_stream.iter_content(1024):
                handle.write(block)

        # Update the response_data
        return_data['location'] = file_name
        return_data['caption'] = info['title']

    except Exception, e:
        logger.error('Google Image lookup failed with: {error}'.format(
            error = str(e)))
        return return_data

    return return_data

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

    # Remove the trigger command
    for command in commands():
        text = ignore_case_replace(command, '', text).strip()

    possible_images = ask_google(text)

    if possible_images['failed']:
        return {
            'location': static_values.data_dir + '/no_image.png',
            'caption': 'Image retreival failed. See logs for details.'
        }

    location_and_caption = save_image(
        random.choice(possible_images['urls']))

    return location_and_caption
