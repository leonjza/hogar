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
import re
import urlparse
from os.path import splitext

def ignore_case_replace (search, replace, string, occurance = 1):
    '''
        Replace a search term in a string, ignoring case.

        :param search: str      The term to search for
        :param replace: str     The term to replace with
        :param string: str      The string to search the term for
        :param occurance: int   The amount of occurances to replace
        :return: str
    '''
    insensitive_search_word = re.compile(re.escape(search), re.IGNORECASE)

    # We keep replacing the result as there could be more
    # than one keyword to work with
    return insensitive_search_word.sub(replace, string, occurance)

def get_url_extention (url):
    '''
        Return the extention from a URL

        :param url:str
        :return:str
    '''
    parsed = urlparse.urlparse(url)
    root, ext = splitext(parsed.path)

    return ext
