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
        q = await self._rabbit.declare_queue(Config.MESSAGES_QUEUE)
        await q.consume(callback=self._callback)
