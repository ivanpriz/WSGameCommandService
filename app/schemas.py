from dataclasses import dataclass
from enum import Enum
from typing import Optional, Any, Literal

from dataclasses_json import dataclass_json


class CommandMethods(Enum):
    MOVE = "MOVE"
    JOIN = "JOIN"
    DISCONNECT = "DISCONNECT"


@dataclass_json
@dataclass
class Command:
    user_id: str
    user_color: str
    username: str
    method: Literal[CommandMethods.MOVE.value, CommandMethods.JOIN.value, CommandMethods.DISCONNECT.value]
    payload: Optional[list[int]] = None


class ResponseMethods(Enum):
    UPDATE_BOARD = "UPDATE_BOARD"
    MSG = "MSG"


class MessagesLevels(Enum):
    INFO = "INFO"
    DEBUG = "DEBUG"
    ERROR = "ERROR"


@dataclass_json
@dataclass
class Response:
    method: Literal[ResponseMethods.UPDATE_BOARD.value]
    success: bool
    payload: Optional


@dataclass_json
@dataclass
class Message:
    level: Literal[MessagesLevels.ERROR.value, MessagesLevels.INFO.value, MessagesLevels.DEBUG.value]
    text: str
    method: Literal[ResponseMethods.MSG.value] = ResponseMethods.MSG.value
    success: bool = True


class EnvironmentObjectColors(Enum):
    SNOW = "#FFFAFA"
    STONE = "#5A5A5A"


class EnvironmentObjectsValues(Enum):
    SNOW = "0"
    STONE = "1"


environment_mapping = {
    EnvironmentObjectsValues.SNOW.value: EnvironmentObjectColors.SNOW.value,
    EnvironmentObjectsValues.STONE.value: EnvironmentObjectColors.STONE.value,
}
