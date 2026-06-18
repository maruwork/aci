import asyncio


async def run():
    task = asyncio.create_task(worker())
    return await task


async def worker():
    return 1
