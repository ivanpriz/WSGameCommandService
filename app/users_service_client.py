import json

from app.rabbit import Rabbit, RPCClient
from app.config import Config
from app.utils.logging import get_logger


class UsersServiceClient:
    _logger = get_logger("UsersServiceClient")

    def __init__(self, rabbit: Rabbit):
        self.rabbit = rabbit
        self.users_create_rpc_client = RPCClient(
            rabbit=rabbit,
            publish_routing_key=Config.USERS_TO_CREATE_QUEUE,
        )
        self.users_delete_rpc_client = RPCClient(
            rabbit=rabbit,
            publish_routing_key=Config.USERS_TO_DELETE_QUEUE,
        )

    async def start(self):
        self._logger.debug("Going to start users api client...")
        await self.users_create_rpc_client.start()
        await self.users_delete_rpc_client.start()
        self._logger.debug("Users api client started!")

    async def create_user(self, conn_id: str):
        self._logger.debug("Goin to create user for conn_id %s", conn_id)
        response = await self.users_create_rpc_client.call(conn_id)
        payload = json.loads(response)
        self._logger.debug(
            "Got response from %s with payload: %s",
            self.users_create_rpc_client.publish_routing_key,
            payload,
        )
        conn_id, username, color = payload["conn_id"], payload["username"], payload["color"]
        return conn_id, username, color

    async def delete_user(self, conn_id: str):
        self._logger.debug("Goin to delete user for conn_id %s", conn_id)
        response = await self.users_delete_rpc_client.call(conn_id)
        payload = json.loads(response)
        self._logger.debug(
            "Got response from %s with payload: %s",
            self.users_delete_rpc_client.publish_routing_key,
            payload,
        )
        conn_id, deleted = payload["conn_id"], payload["deleted"]
        return conn_id, deleted
