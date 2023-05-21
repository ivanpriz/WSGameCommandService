import random

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

    def __init__(self, rabbit: Rabbit):
        self.rabbit = rabbit
        self.renderer_rpc_client = RPCClient(
            rabbit=self.rabbit,
            publish_routing_key=Config.RENDER_BOARD_QUEUE,
        )

    async def process_command(self, command: Command):
        if command.method == CommandMethods.MOVE.value:
            try:
                response = await self.renderer_rpc_client.call(
                    data=command.to_json(),
                    content_type="application/json",
                )
                return Response.from_json(response)

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload=None,
                )

        elif command.method == CommandMethods.JOIN.value:
            try:
                response = await self.renderer_rpc_client.call(
                    data=command.to_json(),
                    content_type="application/json",
                )
                return Response.from_json(response)

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload=None
                )

        elif command.method == CommandMethods.DISCONNECT.value:
            try:
                response = await self.renderer_rpc_client.call(
                    data=command.to_json(),
                    content_type="application/json",
                )
                return Response.from_json(response)

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload={
                        "board": None,
                    }
                )

        else:
            raise Exception(f"Command method {command.method} not supported!")

    async def start(self):
        self._logger.debug("Going to start users api client...")
        await self.renderer_rpc_client.start()
        self._logger.debug("Users api client started!")
