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
import os

class values(object):
    '''
        Static values used by Hogar

        Items such as versioning, API endpoints etc
        are recorded here. This makes it easy to
        change and take affect app wide.
    '''

    version = '1.1'
    data_dir = os.path.abspath(
        os.path.join(os.path.dirname(__file__), '../var/'))
    telegram_api_endpoint = 'https://api.telegram.org/bot{token}/{method}?{options}'
    headers = {
        'Accept': 'application/json'
    }
    verify_ssl = True
    possible_message_types = [
        'text', 'audio', 'document', 'photo', 'sticker', 'video', 'contact', 'location'
    ]
