import asyncio
from typing import Awaitable, Callable, Optional
import json

import aioredis


async def subscribe_with_callback(
        client: aioredis.client.Redis,
        topic_name: str,
        callback: Awaitable,
        delay: int = 0,
        data_parser: Optional[Callable] = json.loads
):
    subscriber = client.pubsub()
    await subscriber.subscribe(topic_name)

    # First msg will contain 1 to inform that we subscribed
    while True:
        message = await subscriber.get_message()
        if message:
            if int(message["data"]) != 1:
                raise Exception("Not 1 received as first msg!")
            break

    while True:
        message = await subscriber.get_message()
        if message:
            if data_parser:
                message["data"] = data_parser(message["data"])
            await callback(message["data"])
        else:
            await asyncio.sleep(delay)
