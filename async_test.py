import asyncio


async def async_foo():
    print("async_foo started")
    await asyncio.sleep(1)
    print("async_foo done")


async def Timeout(timeout_cb, ival, nticks = 1, *cb_params):
    await asyncio.sleep(ival)
    timeout_cb()
    #el = ED2.regTimer(timeout_cb, ival, nticks, False, *cb_params)
    #el.go()
    #return el

def sepp():
    print('sepp')

async def main():
    asyncio.ensure_future(async_foo())  # fire and forget async_foo()
    # btw, you can also create tasks inside non-async funcs
    #asyncio.ensure_future(Timeout(sepp, 1))
    asyncio.create_task(Timeout(sepp, 1))
    print('Do some actions 1')
    await asyncio.sleep(1)
    print('Do some actions 2')
    await asyncio.sleep(1)
    print('Do some actions 3')


if __name__ == '__main__':
    loop = asyncio.new_event_loop()
    loop.create_task(Timeout(sepp, 1))
    #loop = asyncio.get_event_loop()
    loop.run_until_complete(main())