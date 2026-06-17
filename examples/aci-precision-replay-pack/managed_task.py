import asyncio


async def launch():
    task = asyncio.create_task(worker())
    return await task


async def worker():
    return 1
