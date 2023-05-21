from contextlib import asynccontextmanager
from pprint import pprint

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
from fastapi.middleware.cors import CORSMiddleware

from .connection_manager import ConnectionManager
from .users_service_client import UsersServiceClient
from .render_service_client import RenderServiceClient
from .logs_receiver import LogsReceiver
from .utils.logging import get_logger
from .rabbit import Rabbit
from .config import Config
from .schemas import Command, Response, Message, MessagesLevels


conn_manager = ConnectionManager()


async def process_log(log: Message, conn_id: str):
    if log.level in [MessagesLevels.ERROR.value, MessagesLevels.DEBUG.value]:
        await conn_manager.send_data_privately(log.to_dict(), conn_id)
    else:  # INFO
        pprint(log.to_dict())
        await conn_manager.broadcast(log.to_dict())


rabbit = Rabbit(Config.RABBITMQ_URI)
user_service_client = UsersServiceClient(rabbit)
render_service_client = RenderServiceClient(rabbit)
logs_receiver = LogsReceiver(rabbit, process_log=process_log)
logger = get_logger("App")


@asynccontextmanager
async def lifespan(app: FastAPI):
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


async def process_response(response: Response):
    pprint(response)

    if response.success:
        await conn_manager.broadcast(response.to_dict())
        print(f"Broadcasted {response.to_dict()}")


@app.websocket("/ws")
async def websocket_endpoint(websocket: WebSocket):
    conn_id = await conn_manager.connect(websocket)
    _, username, color = await user_service_client.create_user(conn_id)

    result = await render_service_client.process_command(
        Command(
            user_id=str(conn_id),
            user_color=color,
            username=username,
            method="JOIN",
            payload=[],
        )
    )

    await process_response(result)

    while True:
        try:
            data = await websocket.receive_json()
            # TODO Here we will send command to render service via _rabbit
            # TODO after receiving the result we will send updated state to players
            result = await render_service_client.process_command(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method=data["method"],
                    payload=[int(d) for d in data["payload"]],
                )
            )
            await process_response(result)

        except WebSocketDisconnect:
            conn_id, deleted = await user_service_client.delete_user(conn_id)
            print(f"User {conn_id} deleted!")
            result = await render_service_client.process_command(
                Command(
                    user_id=str(conn_id),
                    user_color=color,
                    username=username,
                    method="DISCONNECT",
                    payload=[],
                )
            )
            conn_manager.disconnect(websocket)
            await process_response(result)
            break
