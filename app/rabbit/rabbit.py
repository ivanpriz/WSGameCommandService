from typing import Optional

import aio_pika

from app.utils.logging import get_logger


class Rabbit:
    _logger = get_logger("Rabbit")

    def __init__(self, uri: str):
        self._connection = aio_pika.RobustConnection(uri)
        self.channel: Optional[aio_pika.Channel] = None

    async def connect(self):
        await self._connection.connect()
        self._logger.debug("Connected to Rabbit")

    @property
    def is_connected(self):
        # TODO due to some aiopika issues this method should work different
        return not self._connection.is_closed or self._connection

    @property
    def channel_is_opened(self):
        return not self.channel.is_closed or not self.channel

    async def create_channel(self):
        if not self.channel:
            self.channel = await self._connection.channel()
            await self.channel.set_qos(prefetch_count=1)
            self._logger.debug("Created Rabbit _connection channel")
        elif self.channel.is_closed:
            await self.channel.reopen()
            self._logger.debug("Reopened Rabbit _connection channel")
        else:
            self._logger.debug("Trying to create Rabbit channel while already having opened one!")

    async def close_channel(self):
        if self.channel:
            await self.channel.close()
            self._logger.debug("Closed Rabbit channel")
        else:
            self._logger.debug("Trying to close Rabbit channel while not having one!")

    async def close(self):
        await self.close_channel()
        if self._connection:
            await self._connection.close()
            self._logger.debug("Closed Rabbit _connection")
        else:
            self._logger.debug("Trying to close Rabbit _connection while not having one!")

    async def declare_queue(
            self,
            name: Optional[str] = None,
            durable: bool = True,
            exclusive: bool = False
    ):
        """Declares queue"""
        if not self.channel or self.channel.is_closed:
            raise Exception("No channel to declare queue!")
        return await self.channel.declare_queue(name, durable=durable, exclusive=exclusive)
