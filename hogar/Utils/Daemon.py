# The MIT License (MIT)
#
# Copyright (c) 2015 Leon Jacobs
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the 'Software'), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED 'AS IS', WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.

'''
    Generic Daemon Class:
    Source: https://github.com/serverdensity/python-daemon
'''

# Core modules
import atexit
import os
import sys
import time
import signal

class Daemon(object):
    '''
        A generic daemon class.

        Usage: subclass the Daemon class and override the run() method
    '''

    def __init__ (self, pidfile, stdin = os.devnull,
                  stdout = os.devnull, stderr = os.devnull,
                  home_dir = '.', umask = 022, verbose = 1, use_gevent = False):

        self.stdin = stdin
        self.stdout = stdout
        self.stderr = stderr
        self.pidfile = pidfile
        self.home_dir = home_dir
        self.verbose = verbose
        self.umask = umask
        self.daemon_alive = True
        self.use_gevent = use_gevent

    def daemonize (self):

        '''
            Do the UNIX double-fork magic, see Stevens' 'Advanced
            Programming in the UNIX Environment' for details (ISBN 0201563177)
            http://www.erlenstar.demon.co.uk/unix/faq_2.html#SEC16
        '''

        try:

            pid = os.fork()
            if pid > 0:
                # Exit first parent
                sys.exit(0)

        except OSError, e:

            sys.stderr.write(
                'fork #1 failed: %d (%s)\n' % (e.errno, e.strerror))

            sys.exit(1)

        # Decouple from parent environment
        os.chdir(self.home_dir)
        os.setsid()
        os.umask(self.umask)

        # Do second fork
        try:

            pid = os.fork()
            if pid > 0:
                # Exit from second parent
                sys.exit(0)

        except OSError, e:

            sys.stderr.write(
                'fork #2 failed: %d (%s)\n' % (e.errno, e.strerror))

            sys.exit(1)

        # This block breaks on OS X
        if sys.platform != 'darwin':

            # Redirect standard file descriptors
            sys.stdout.flush()
            sys.stderr.flush()
            si = file(self.stdin, 'r')
            so = file(self.stdout, 'a+')

            if self.stderr:
                se = file(self.stderr, 'a+', 0)
            else:
                se = so

            os.dup2(si.fileno(), sys.stdin.fileno())
            os.dup2(so.fileno(), sys.stdout.fileno())
            os.dup2(se.fileno(), sys.stderr.fileno())

        def sigtermhandler (signum, frame):

            self.daemon_alive = False
            sys.exit()

        if self.use_gevent:

            import gevent
            gevent.reinit()
            gevent.signal(signal.SIGTERM, sigtermhandler, signal.SIGTERM, None)
            gevent.signal(signal.SIGINT, sigtermhandler, signal.SIGINT, None)

        else:

            signal.signal(signal.SIGTERM, sigtermhandler)
            signal.signal(signal.SIGINT, sigtermhandler)

        if self.verbose >= 1:
            print 'Started'

        # Make sure pid file is removed if we quit
        atexit.register(self.delpid)

        # Write pidfile
        pid = str(os.getpid())
        file(self.pidfile, 'w+').write('%s\n' % pid)

    def delpid (self):
        os.remove(self.pidfile)

    def start (self, *args, **kwargs):

        '''
            Start the daemon
        '''

        if self.verbose >= 1:
            print 'Starting...'

        # Check for a pidfile to see if the daemon already runs
        try:

            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()

        except IOError:
            pid = None

        except SystemExit:
            pid = None

        if pid:
            message = 'pidfile %s already exists. Is it already running?\n'
            sys.stderr.write(message % self.pidfile)
            sys.exit(1)

        # Start the daemon
        self.daemonize()
        self.run(*args, **kwargs)

    def stop (self):

        '''
            Stop the daemon
        '''

        if self.verbose >= 1:
            print 'Stopping...'

        # Get the pid from the pidfile
        pid = self.get_pid()

        if not pid:

            message = 'pidfile %s does not exist. Not running?\n'
            sys.stderr.write(message % self.pidfile)

            # Just to be sure. A ValueError might occur if the PID file is
            # empty but does actually exist
            if os.path.exists(self.pidfile):
                os.remove(self.pidfile)

            return  # Not an error in a restart

        # Try killing the daemon process
        try:

            i = 0
            while 1:

                os.kill(pid, signal.SIGTERM)
                time.sleep(0.1)
                i += 1
                if i % 10 == 0:
                    os.kill(pid, signal.SIGHUP)

        except OSError, err:

            err = str(err)
            if err.find('No such process') > 0:
                if os.path.exists(self.pidfile):
                    os.remove(self.pidfile)

            else:
                print str(err)
                sys.exit(1)

        if self.verbose >= 1:
            print 'Stopped'

    def restart (self):

        '''
            Restart the daemon
        '''

        self.stop()
        self.start()

    def get_pid (self):

        try:

            pf = file(self.pidfile, 'r')
            pid = int(pf.read().strip())
            pf.close()

        except IOError:
            pid = None

        except SystemExit:
            pid = None

        return pid

    def is_running (self):

        pid = self.get_pid()

        if pid is None:
            print 'Process is stopped'
        elif os.path.exists('/proc/%d' % pid):
            print 'Process (pid %d) is running...' % pid
        else:
            print 'Process (pid %d) is killed' % pid

        return pid and os.path.exists('/proc/%d' % pid)

    def run (self):

        '''
            You should override this method when you subclass Daemon.
            It will be called after the process has been
        daemonized by start() or restart().
        '''

        raise NotImplementedError
