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

from multiprocessing import Pool
from hogar.Jobs import Reminder
import schedule
import time
import os
import sys
import logging

logger = logging.getLogger(__name__)

# The schedule package is pretty noisy. Reduce that.
logging.getLogger('schedule').setLevel(logging.WARNING)

def scheduler_init (parent):
    '''
        Schedule Init

        Start the main loop for the internal scheduler that
        ticks every second.

        --
        @param  parent:int  The PID of the parent.

        @return void
    '''

    # Define the jobs to run at which intervals
    schedule.every().minute.do(Reminder.run_remind_once)
    schedule.every().minute.do(Reminder.run_remind_recurring)

    # Start the main thread, polling the schedules
    # every second
    while True:

        # Check if the current parent pid matches the original
        # parent that started us. If not, we should end.
        if os.getppid() != parent:
            logger.error(
                'Killing scheduler as it has become detached from parent PID.')

            sys.exit(1)

        # Run the schedule
        schedule.run_pending()
        time.sleep(1)

    return

def boot (ppid):
    '''
        Boot

        Starts the Scheduler

        --
        @param  ppid:int    The PID of the parent.

        @return None
    '''

    pool = Pool(processes = 1)
    logger.debug('Started scheduler pool with 1 process')

    pool.apply_async(scheduler_init, args = (ppid,))
    logger.debug('Started async scheduler_init()')

    return
