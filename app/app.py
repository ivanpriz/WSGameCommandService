import asyncio
from contextlib import asynccontextmanager
from pprint import pprint
from typing import Optional

import aioredis
from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .connection_manager import ConnectionManager
from .users_service_client import UsersServiceClient
from .render_service_client import RenderServiceClient
from .logs_receiver import LogsReceiver
from .utils.logging import get_logger
from .utils.redis import subscribe_with_callback
from .rabbit import Rabbit
from .config import Config
from .schemas import Command, Response, Message, MessagesLevels


conn_manager = ConnectionManager()
redis_pub_client: Optional[aioredis.client.Redis] = None
redis_sub_client: Optional[aioredis.client.Redis] = None


async def process_log(log: Message, conn_id: str):
    if log.level in [MessagesLevels.ERROR.value, MessagesLevels.DEBUG.value]:
        await conn_manager.send_data_privately(log.to_dict(), conn_id)
    else:  # INFO
        await conn_manager.broadcast(log.to_dict())


async def process_rendered_board(response: Response):
    if response.success:
        await redis_pub_client.publish(Config.REDIS_TOPIC_NAME, response.to_json())


rabbit = Rabbit(Config.RABBITMQ_URI)
user_service_client = UsersServiceClient(rabbit)
render_service_client = RenderServiceClient(rabbit, process_board=process_rendered_board)
logs_receiver = LogsReceiver(rabbit, process_log=process_log)
logger = get_logger("App")


@asynccontextmanager
async def lifespan(app: FastAPI):
    global redis_sub_client
    global redis_pub_client
    redis_sub = aioredis.from_url(Config.REDIS_URL, encoding="utf-8", decode_responses=True)
    redis_pub = aioredis.from_url(Config.REDIS_URL, encoding="utf-8", decode_responses=True)
    redis_sub_client = await redis_sub.client()
    redis_pub_client = await redis_pub.client()

    await rabbit.connect()
    await rabbit.create_channel()
    await user_service_client.start()
    await render_service_client.start()
    await logs_receiver.start()

    yield

    await rabbit.close_channel()
    await rabbit.close()


app = FastAPI(lifespan=lifespan)

app.mount("/static", StaticFiles(directory="static"), name="static")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"]
)


@app.get("/")
async def get():
    with open("./static/game_client.html", "r") as f:
        return HTMLResponse(f.read())


async def redis_msg_callback(redis_msg: dict):
    await conn_manager.broadcast(redis_msg)


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    asyncio.create_task(subscribe_with_callback(redis_sub_client, Config.REDIS_TOPIC_NAME, redis_msg_callback))
    conn_id = await conn_manager.connect(websocket)

    _, username, color = await user_service_client.create_user(conn_id)

    await render_service_client.render_board(
        Command(
            user_id=str(conn_id),
            user_color=color,
            username=username,
            method="JOIN",
            payload=[],
        )
    )

    while True:
        try:
            data = await websocket.receive_json()
            # TODO Here we will send command to render service via _rabbit
            # TODO after receiving the result we will send updated state to players
            await render_service_client.render_board(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method=data["method"],
                    payload=[int(d) for d in data["payload"]],
                )
            )

        except WebSocketDisconnect:
            conn_id, deleted = await user_service_client.delete_user(conn_id)
            await render_service_client.render_board(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method="DISCONNECT",
                    payload=[],
                )
            )
            conn_manager.disconnect(websocket)
            break
