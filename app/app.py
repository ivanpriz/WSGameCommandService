import asyncio
from contextlib import asynccontextmanager
from pprint import pprint
from functools import partial

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .connection_manager import ConnectionManager
from .users_service_api import UsersServiceApi
from .render_server_api import RenderServerAPI
from .utils.logging import get_logger
from .rabbit import Rabbit
from .config import Config
from .schemas import Command, Response, Message, MessagesLevels


conn_manager = ConnectionManager()
render_server = RenderServerAPI()
rabbit = Rabbit(Config.RABBITMQ_URI)
user_service_api = UsersServiceApi(rabbit)
logger = get_logger("App")


@asynccontextmanager
async def lifespan(app: FastAPI):
    await rabbit.connect()
    await rabbit.create_channel()
    await user_service_api.start()
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
    with open("./static/frontend2.html", "r") as f:
        return HTMLResponse(f.read())


async def process_message(websocket: WebSocket, msg: Message):
    if msg.level in [MessagesLevels.ERROR.value, MessagesLevels.DEBUG.value]:
        await conn_manager.send_data_privately(msg.to_dict(), websocket)
    else:  # INFO
        pprint(msg.to_dict())
        await conn_manager.broadcast(msg.to_dict())


async def process_response(websocket: WebSocket, response: Response, messages: list[Message]):
    pprint(response)

    if response.success:
        await conn_manager.broadcast(response.to_dict())

    await asyncio.gather(*[asyncio.create_task(process_message(websocket, msg)) for msg in messages])


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    _process_response = partial(process_response, websocket)

    conn_id = await conn_manager.connect(websocket)
    _, username, color = await user_service_api.create_user(conn_id)

    result, msgs = await render_server.process_command(
        Command(
            user_id=str(conn_id),
            user_color=color,
            username=username,
            method="JOIN",
            payload=[],
        )
    )

    await _process_response(result, msgs)

    while True:
        try:
            data = await websocket.receive_json()
            # TODO Here we will send command to render service via rabbit
            # TODO after receiving the result we will send updated state to players
            result, msgs = await render_server.process_command(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method=data["method"],
                    payload=[int(d) for d in data["payload"]],
                )
            )
            await _process_response(result, msgs)

        except WebSocketDisconnect:
            conn_id, deleted = await user_service_api.delete_user(conn_id)
            print(f"User {conn_id} deleted!")
            result, msgs = await render_server.process_command(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method="DISCONNECT",
                    payload=[],
                )
            )
            conn_manager.disconnect(websocket)
            await process_response(websocket, result, msgs)
            break

