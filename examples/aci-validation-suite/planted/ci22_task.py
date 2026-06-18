import asyncio


async def run():
    asyncio.create_task(worker())


async def worker():
    return 1
