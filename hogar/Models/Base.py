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
from peewee import *
from playhouse.pool import PooledMySQLDatabase
from playhouse.sqlite_ext import SqliteExtDatabase
import ConfigParser

config = ConfigParser.ConfigParser()
config.read(
    os.path.join(os.path.dirname(__file__), '../../settings.ini'))

db_engine = config.get('main', 'db_engine')

# setup a db instance based on the connection to use
if db_engine == 'sqlite':

    db_name = config.get('sqlite', 'database_location')
    db = SqliteExtDatabase(db_name, threadlocals = True, journal_mode = 'WAL')

elif db_engine == 'mysql':

    db_username = config.get('mysql', 'username')
    db_password = config.get('mysql', 'password')
    db_database = config.get('mysql', 'database')
    db_dbhost = config.get('mysql', 'host')

    db = PooledMySQLDatabase(
        db_database,
        max_connections = 32,
        stale_timeout = 300,
        host = db_dbhost,
        user = db_username,
        passwd = db_password
    )
else:
    raise Exception('Invalid db_engine option in settings file.')

class BaseModel(Model):
    ''' The base database Model '''

    class Meta:
        database = db
