import asyncio


async def launch():
    asyncio.create_task(worker())


async def worker():
    return 1
