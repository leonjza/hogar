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

''' A Chat Logger '''

from hogar.static import values as static_values

from hogar.Models.Base import db
from hogar.Models.Logger import Logger

import logging
logger = logging.getLogger(__name__)

def applicable_types():

    '''
        Applicable Types

        Returns the type of messages this plugin is for.
        See: hogar.static.values

        --
        @return list
    '''

    return static_values.possible_message_types

def commands():

    '''
        Commands

        In the case of text plugins, returns the commands
        that this plugin should trigger for. For other
        message types, a empty list should be returned.

        --
        @return list
    '''

    return ['*']    # all commands

def should_reply():

    '''
        Should Reply

        Specifies wether a reply should be sent to the original
        sender of the message that triggered this plugin.

        --
        @return bool
    '''

    return False

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

def _process_from(message, record):

    '''
        Process From

        Take a Telegram Message payload as well as a Hogar
        Logger Model and populate the from_* information

        --
        @param  message:dict    The message sent by the user
        @param  record:object   The hogar.Models.Logger.Logger object

        @return str
    '''

    # from_username = CharField(null = True, max_length = 250)
    # from_first_name = CharField(null = True, max_length = 250)
    # from_last_name = CharField(null = True, max_length = 250)
    # from_id = IntegerField()

    # u'from':{
    #   u'username':u'username',
    #   u'first_name':u'first',
    #   u'last_name':u'last',
    #   u'id':12345
    # },

    if 'username' in message['from']:
        record.from_username = message['from']['username']

    if 'first_name' in message['from']:
        record.from_first_name = message['from']['first_name']

    if 'last_name' in message['from']:
        record.from_last_name = message['from']['last_name']

    if 'id' in message['from']:
        record.from_id = message['from']['id']

    return record

def _process_chat(message, record):

    '''
        Process Chat

        Take a Telegram Message payload as well as a Hogar
        Logger Model and populate the chat_* information

        --
        @param  message:dict    The message sent by the user
        @param  record:object   The hogar.Models.Logger.Logger object

        @return str
    '''


    # chat_title = CharField(null = True, max_length = 250)
    # chat_id = IntegerField()
    # chat_username= CharField(null = True, max_length = 250)
    # chat_first_name = CharField(null = True, max_length = 250)
    # chat_last_name = CharField(null = True, max_length = 250)

    # u'chat':{
    #   u'username':u'dude',
    #   u'first_name':u'first',
    #   u'last_name':u'last',
    #   u'id':12345
    # }

    # u'chat':{
    #   u'id':-12345,
    #   u'title':u'A Group Chat'
    # }

    if 'title' in message['chat']:
        record.chat_title = message['chat']['title']

    if 'id' in message['chat']:
        record.chat_id = message['chat']['id']

    if 'username' in message['chat']:
        record.chat_username = message['chat']['username']

    if 'first_name' in message['chat']:
        record.chat_first_name = message['chat']['first_name']

    if 'last_name' in message['chat']:
        record.chat_last_name = message['chat']['last_name']

    return record

def _process_file_id(message, record):

    '''
        Process File ID

        Take a Telegram Message payload as well as a Hogar
        Logger Model and populate the file_id information

        --
        @param  message:dict    The message sent by the user
        @param  record:object   The hogar.Models.Logger.Logger object

        @return str
    '''


    # If we are a photo:
    # u'photo':[
    #   {
    #      u'width':90,
    #      u'file_size':1458,
    #      u'file_id':u'123-AEAAQI',
    #      u'height':90
    #   }
    # ],
    if 'photo' in message:
        record.file_id = message['photo'][0]['file_id']

    # u'sticker':{
    #   u'width':482,
    #   u'height':512,
    #   u'thumb':{
    #      u'width':84,
    #      u'file_size':2658,
    #      u'file_id':u'123-AEAAQI',
    #      u'height':90
    #   },
    #   u'file_id':u'BQADBAADOAADyIsGAAGV20QAAasOeuMC',
    #   u'file_size':43636
    # },
    elif 'sticker' in message:
        record.file_id = message['sticker']['file_id']

    # u'audio':{
    #   u'duration':1,
    #   u'file_id':u'123-AEAAQI',
    #   u'mime_type':u'audio/ogg',
    #   u'file_size':9162
    # },
    elif 'audio' in message:
        record.file_id = message['audio']['file_id']

    # u'document':{
    #   u'file_name':u'test.js',
    #   u'file_id':u'123-AEAAQI',
    #   u'thumb':{},
    #   u'mime_type':u'application/javascript',
    #   u'file_size':34728
    # },
    elif 'document' in message:
        record.file_id = message['document']['file_id']

    # return
    return record

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

    # Search for the message type
    type = [message_type for message_type in static_values.possible_message_types \
        if message_type in message]

    # Gran the first entry in the above list.
    # Should never have more than one anyways.
    type = type[0]

    # Check if we already know about this message.
    # Honestly can't think of a case were this
    # will actually happen. Nonetheless, lets
    # check and warn.
    try:
        l = Logger.get(Logger.message_id == message['message_id'])
        logger.warning('Message {id} already exists in the database.'.format(
            id = message['message_id']
        ))
        return

    except Logger.DoesNotExist:

        # Nope. Create it!
        logger.debug('Storing message id {id} which is a {type} message'.format(
            id = message['message_id'],
            type = type
        ))

        # Start a new Logger instance
        l = Logger(message_id = message['message_id'])

    # Set some fields that are always applicable
    # to any message type
    l.message_type = type
    l.telegram_date = message['date']

    # Populate the 'from' details
    l = _process_from(message, l)

    # Populate the 'chat' details. Chat
    # is the actual person/room the
    # came from
    l = _process_chat(message, l)

    # Process any potential file_id's
    l = _process_file_id(message, l)

    # If there is text, add that too
    l.text = message['text'] if 'text' in message else None

    # Aaand save.
    l.save()

    return
