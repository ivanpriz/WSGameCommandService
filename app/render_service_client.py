import asyncio
import random

import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.schemas import (
    CommandMethods,
    Command,
    EnvironmentObjectColors,
    EnvironmentObjectsValues,
    Response,
    ResponseMethods,
    Message,
    MessagesLevels,
)
from app.rabbit import Rabbit, RPCClient
from app.utils.logging import get_logger
from app.config import Config


class RenderServiceClient:
    _logger = get_logger("RenderServiceClient")

    def __init__(self, rabbit: Rabbit, process_board):
        self.rabbit = rabbit
        self.boards_to_render_queue = None
        self.rendered_boards_queue = None
        self._process_rendered_board = process_board

    async def render_board(self, command: Command):
        await self.rabbit.channel.default_exchange.publish(
            aio_pika.Message(
                body=command.to_json().encode("utf-8"),
                content_type="application/json",
            ),
            routing_key=Config.BOARDS_TO_RENDER_QUEUE
        )

    async def _callback(self, rabbit_msg: AbstractIncomingMessage):
        async with rabbit_msg.process():
            payload = rabbit_msg.body.decode()
            self._logger.debug("Received board: %s", payload)
            board = Message.from_json(payload)
            self._logger.debug("Processing board %s", board)
            await self._process_rendered_board(board)

    async def start(self):
        self._logger.debug("Going to start users api client...")
        self.boards_to_render_queue = await self.rabbit.declare_queue(
            Config.BOARDS_TO_RENDER_QUEUE,
            durable=True,
        )
        self.rendered_boards_queue = await self.rabbit.declare_queue(
            Config.RENDERED_BOARDS_QUEUE,
            durable=True,
        )
        asyncio.create_task(
            self.rendered_boards_queue.consume(
                callback=self._callback
            )
        )
        self._logger.debug("Render service client started!")
