# Copyright (c) 2003-2005 Maxim Sobolev. All rights reserved.
# Copyright (c) 2006-2018 Sippy Software, Inc. All rights reserved.
#
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification,
# are permitted provided that the following conditions are met:
#
# 1. Redistributions of source code must retain the above copyright notice, this
# list of conditions and the following disclaimer.
#
# 2. Redistributions in binary form must reproduce the above copyright notice,
# this list of conditions and the following disclaimer in the documentation and/or
# other materials provided with the distribution.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT HOLDER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON
# ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

from threading import Lock
from random import random
import asyncio
from sippy.Time.MonoTime import MonoTime


async def TimeoutTask(timeout_cb, ival, cb_params):
    await asyncio.sleep(ival)
    timeout_cb(*cb_params)


async def ImmediateTask(task_cb, cb_params):
    await asyncio.sleep(0)
    task_cb(*cb_params)


async def PeriodicTask(task_cb, ival, cb_params):
    while True:
        await asyncio.sleep(ival)
        task_cb(*cb_params)


class Singleton(object):
    '''Use to create a singleton'''
    __state_lock = Lock()

    def __new__(cls, *args, **kwds):
        '''
        >>> s = Singleton()
        >>> p = Singleton()
        >>> id(s) == id(p)
        True
        '''
        sself = '__self__'
        cls.__state_lock.acquire()
        if not hasattr(cls, sself):
            instance = object.__new__(cls)
            instance.__sinit__(*args, **kwds)
            setattr(cls, sself, instance)
        cls.__state_lock.release()
        return getattr(cls, sself)

    def __sinit__(self, *args, **kwds):
        pass


class EventDispatcher2(Singleton):
    loop = None

    def get_randomizer(self, p):
        return lambda x: x * (1.0 + p * (1.0 - 2.0 * random()))

    def __init__(self, freq=100.0):
        self.evloop = asyncio.new_event_loop()
        self.randomizer = self.get_randomizer(0.1)

    def loop(self, timeout=None, freq=None):
        self.evloop.run_forever()

    def breakLoop(self, rval=0):
        self.evloop.stop()

    def regTimer(self, timer_cb, ival, nticks=1, abs_time=False, *cb_params) -> asyncio.Task:
        diff = 0
        if abs_time:
            if not isinstance(ival, MonoTime):
                raise TypeError('ival is not MonoTime')
            diff = ival.offsetFromNow()  # ival - MonoTime()
        else:
            diff = self.randomizer(ival)

        if nticks == -1:
            return self.evloop.create_task(PeriodicTask(timer_cb, diff, cb_params))
        else:
            return self.evloop.create_task(TimeoutTask(timer_cb, diff, cb_params))

    def callFromThread(self, thread_cb, *cb_params):
        self.evloop.create_task(ImmediateTask(thread_cb, cb_params))
        # thread_cb(*cb_params)


ED2 = EventDispatcher2()
