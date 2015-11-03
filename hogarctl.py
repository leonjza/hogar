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

__author__ = 'Leon Jacobs'

import os
import sys
import logging
import ConfigParser

from hogar.static import values as static_values
from hogar.Utils import PluginLoader
from hogar.Utils.DBUtils import DB
from hogar.Models.Base import db

from hogar.core import App

# read the required configuration
config = ConfigParser.ConfigParser()
config.read(
    os.path.join(os.path.dirname(__file__), 'settings.ini'))

# set up logging to file
logging.basicConfig(
    level = logging.DEBUG,
    format = '%(asctime)s %(processName)-10s %(name)s %(levelname)-8s %(message)s',
    datefmt = '%Y-%m-%d %H:%M:%S',
    filename = os.path.dirname(os.path.realpath(__file__)) + '/var/hogar.log',
    filemode = 'a'
)
logger = logging.getLogger(__name__)

# make some sub modules stfu
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('peewee').setLevel(logging.INFO)
logging.getLogger('requests').setLevel(logging.WARNING)

def banner ():
    '''
        Print the Hogar Banner

        --
        @return None
    '''

    return '''
.__
|  |__   ____   _________ _______
|  |  \ /  _ \ / ___\__  \\\\_  __ \\
|   Y  (  <_> ) /_/  > __ \|  | \/
|___|  /\____/\___  (____  /__|
     \/      /_____/     \/
                   v{v} - @leonjza
    '''.format(v = static_values.version)

def qprint (message):
    '''
        QPrint

        Print a message if we do not have the 'quiet'
        argument

        --
        @return None
        :param message: The message to print
    '''

    if 'quiet' not in sys.argv:
        print message

    return

if __name__ == '__main__':

    '''
        Hogar entry point.

        Running Hogar with __name__ as '__main__' (i.e python start.py) will
        allow Hogar to bootstrap the plugin loading and kick off the main
        routine.

        Providing 'setupdb' as an argument will have Hogar run any datebase
        migrations that may be outstanding.
    '''

    qprint(banner())

    # prepare a db setup command
    if len(sys.argv) > 1:

        # Initiate the Hogar
        app = App(os.path.dirname(
            os.path.realpath(__file__)) + '/var/hogar.pid')

        # The database setup commands
        if sys.argv[1] == 'setupdb':

            logger.debug('Preparing to do database setup')
            DB.setup()
            logger.info('Database succesfully setup')
            print ' * Setup of database `%s` complete' % db.database

            sys.exit(0)

        # The start of hogar as a daemon. Debug is used
        # to keep the controlling terminal attached
        elif sys.argv[1] == 'start' or sys.argv[1] == 'debug':

            qprint(' * Loading plugins...')
            command_map = PluginLoader.prepare_plugins()

            if not command_map:
                qprint(' * No plugins found. Aborting.')
                sys.exit(1)

            qprint(' * Loaded plugins for {number} message types: {commands}'.format(
                number = len(command_map.keys()),
                commands = '; '.join(command_map.keys())))

            # Pass the checked command map to the instance
            # of Hogar
            app.set_command_map(command_map)

            # Decide if we should daemonize or stay attached
            if sys.argv[1] == 'start':

                qprint(' * Starting Daemon')
                app.start()

            else:

                qprint(' * Staying in foreground')
                app.run()

        # Check the status of the daemon
        elif sys.argv[1] == 'status':
            app.is_running()

        # Stop the app
        elif sys.argv[1] == 'stop':
            app.stop()

        else:
            print ' * Supported arguments are: start|stop|restart|setupdb|debug'
            sys.exit(0)

    else:
        print ' * Supported arguments are: start|stop|restart|setupdb|debug'
        sys.exit(1)
