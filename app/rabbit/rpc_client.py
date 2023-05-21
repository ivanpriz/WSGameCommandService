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
        self._logger.debug("Rabbit connected for rpc of q %s", self.publish_routing_key)
        self.callback_queue = await self.rabbit.declare_queue(exclusive=True)
        self._logger.debug("Callback q for q %s decalred!", self.publish_routing_key)
        await self.callback_queue.consume(self._on_response, no_ack=True)
        self._logger.debug("RPC server for q %s started!", self.publish_routing_key)
        return self

    async def _on_response(self, message: AbstractIncomingMessage):
        if message.correlation_id is None:
            self._logger.debug("Message with no corr_id in rpc for q %s: %s!", self.publish_routing_key, message)
            return

        future: asyncio.Future = self.futures.pop(message.correlation_id)
        future.set_result(message.body)
        self._logger.debug("RPC for q %s processed message!", self.publish_routing_key)

    async def call(
            self,
            data: Any,
            data_stringifier: Callable = lambda x: str(x),
            content_type: str = "text/plain"
    ):
        correlation_id = str(uuid.uuid4())
        future = asyncio.Future()

        self.futures[correlation_id] = future

        await self.rabbit.channel.default_exchange.publish(
            aio_pika.Message(
                body=data_stringifier(data).encode("utf-8"),
                content_type=content_type,
                correlation_id=correlation_id,
                reply_to=self.callback_queue.name
            ),
            routing_key=self.publish_routing_key,
        )
        self._logger.debug(
            "RPC client for q %s published msg with corr_id %s",
            self.publish_routing_key,
            correlation_id,
        )

        res = await future
        decoded_res = res.decode()
        self._logger.debug(
            "RPC client for q %s got response %s corr_id %s",
            self.publish_routing_key,
            decoded_res,
            correlation_id,
        )
        return decoded_res
