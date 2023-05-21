import asyncio
import uuid
from typing import Optional, MutableMapping, Any, Callable

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.utils.logging import get_logger


class RPCClient:
    _logger = get_logger("RPC")

    def __init__(self, rabbit, publish_routing_key: str):
        self.rabbit = rabbit
        self.callback_queue: Optional[aio_pika.Queue] = None
        self.futures: MutableMapping[str, asyncio.Future] = {}
        self.publish_routing_key = publish_routing_key

    async def _connect_to_rabbit_if_not(self):
        if not self.rabbit.is_connected:
            await self.rabbit.connect()

        if not self.rabbit.channel or self.rabbit.channel_is_opened:
            await self.rabbit.create_channel()

    async def start(self):
        await self._connect_to_rabbit_if_not()
        self.callback_queue = await self.rabbit.declare_queue(exclusive=True)
        await self.callback_queue.consume(self._on_response, no_ack=True)
        return self

    async def _on_response(self, message: AbstractIncomingMessage):
        if message.correlation_id is None:
            self._logger.debug("Bad message!")
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)

    async def call(
            self,
            data: Any,
            data_preprocessor: Callable = lambda x: str(x).encode("utf-8"),
            content_type: str = "text/plain"
    ):
        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()

        self.futures[correlation_id] = future

        await self.rabbit.channel.default_exchange.publish(
            aio_pika.Message(
                body=data_preprocessor(data),
                content_type=content_type,
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key=self.publish_routing_key,
        )

        res = await future
        return res.decode()