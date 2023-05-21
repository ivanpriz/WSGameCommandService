import asyncio
import uuid

from fastapi import WebSocket


class ConnectionManager:
    """Assigns ids for connections"""
    def __init__(self):
        # We want 2 dicts for search to be faster
        self.active_conns_map_socket_uuid: dict[WebSocket, str] = {}
        self.active_conns_map_uuid_socket: dict[str, WebSocket] = {}

    async def connect(self, websocket: WebSocket):
        await websocket.accept()
        conn_id = str(uuid.uuid4())
        self.active_conns_map_socket_uuid.update({websocket: conn_id})
        self.active_conns_map_uuid_socket.update({conn_id: websocket})
        return conn_id

    def disconnect(self, websocket: WebSocket):
        conn_id = self.active_conns_map_socket_uuid.get(websocket)
        self.active_conns_map_socket_uuid.pop(websocket)
        self.active_conns_map_uuid_socket.pop(conn_id)
        print(f"Connection remaining: {self.active_conns_map_socket_uuid}")
        return conn_id

    async def send_data_privately(self, data: dict, conn_id: str):
        websocket = self.active_conns_map_uuid_socket.get(conn_id, None)
        if websocket:
            await websocket.send_json(data)

    async def broadcast(self, data: dict):
        await asyncio.gather(
            *[
                asyncio.create_task(c.send_json(data))
                for c in self.active_conns_map_socket_uuid.keys()
            ]
        )
