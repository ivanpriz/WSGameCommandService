import aio_pika
from aio_pika.abc import AbstractIncomingMessage

from app.rabbit import Rabbit
from app.config import Config
from app.schemas import Message
from app.utils.logging import get_logger


class LogsReceiver:
    _logger = get_logger("LogsReceiver")

    def __init__(self, rabbit: Rabbit, process_log):
        self._rabbit = rabbit
        self._process_log = process_log

    async def _callback(self, rabbit_msg: AbstractIncomingMessage):
        async with rabbit_msg.process():
            payload = rabbit_msg.body.decode()
            self._logger.debug("Received log: %s", payload)
            log = Message.from_json(payload)
            self._logger.debug("Processing log %s", log)
            await self._process_log(log, log.conn_id)

    async def start(self):
        msgs_exchange = await self._rabbit.declare_exchange(
            Config.MESSAGES_EXCHANGE,
            _type=aio_pika.ExchangeType.FANOUT
        )
        q = await self._rabbit.channel.declare_queue(
            f"MESSAGE_QUEUE_{Config.INSTANCE_ID}",
            durable=True
        )
        await q.bind(exchange=msgs_exchange)
        await q.consume(callback=self._callback)
