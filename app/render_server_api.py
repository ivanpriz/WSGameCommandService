import random

from .schemas import (
    CommandMethods,
    Command,
    EnvironmentObjectColors,
    EnvironmentObjectsValues,
    Response,
    ResponseMethods,
    Message,
    MessagesLevels,
)


class RenderServerAPI:
    def __init__(self):
        self._board = [
            [EnvironmentObjectsValues.SNOW.value for _ in range(3)]
            for _ in range(3)
        ]
        self._colorized_board = [
            [EnvironmentObjectColors.SNOW.value for _ in range(3)]
            for _ in range(3)
        ]
        self._users_positions: dict[str, tuple] = {}

    def _render_board_on_move(self, command: Command) -> list:
        user_id = command.user_id
        user_color = command.user_color
        coord_x = command.payload[0]
        coord_y = command.payload[1]

        if not user_id:
            raise Exception("user_id should be provided")

        # Remove user from previous place
        if user_id not in self._users_positions:
            raise Exception("User not on board!")

        if (coord_x, coord_y) in self._users_positions.values():
            raise Exception("You're trying to move on not free cell!")

        self._board[
            self._users_positions[user_id][1]
        ][
            self._users_positions[user_id][0]
        ] = EnvironmentObjectsValues.SNOW.value
        self._colorized_board[
            self._users_positions[user_id][1]
        ][
            self._users_positions[user_id][0]
        ] = EnvironmentObjectColors.SNOW.value

        # Set new user pos
        self._board[coord_y][coord_x] = user_id
        self._users_positions[user_id] = (coord_x, coord_y)

        # Create colorized board
        self._colorized_board[coord_y][coord_x] = user_color
        return self._colorized_board

    def _render_board_on_join(self, command: Command) -> list:
        user_id = command.user_id
        user_color = command.user_color

        # TODO handle when no space is left
        random_position = None
        while not random_position or random_position in self._users_positions.values():
            random_position = (random.randint(0, 2), random.randint(0, 2))

        self._board[random_position[1]][random_position[0]] = user_id
        self._users_positions[user_id] = random_position
        self._colorized_board[random_position[1]][random_position[0]] = user_color
        return self._colorized_board

    def _render_board_on_disconnect(self, command: Command) -> list:
        user_id = command.user_id

        if not user_id in self._users_positions:
            raise Exception("Not existing user trying to disconnect!")

        user_coords = self._users_positions[user_id]
        self._board[user_coords[1]][user_coords[0]] = EnvironmentObjectsValues.SNOW.value
        self._colorized_board[user_coords[1]][user_coords[0]] = EnvironmentObjectColors.SNOW.value
        self._users_positions.pop(user_id)
        return self._colorized_board

    async def process_command(self, command: Command):
        if command.method == CommandMethods.MOVE.value:
            try:
                colorized_board = self._render_board_on_move(command)
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=True,
                    payload={
                        "board": colorized_board
                    }
                ), [Message(level=MessagesLevels.INFO.value, text=f"User {command.username} moved!")]

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload=None,
                ), [Message(level=MessagesLevels.ERROR.value, text=str(e))]

        elif command.method == CommandMethods.JOIN.value:
            try:
                colorized_board = self._render_board_on_join(command)
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=True,
                    payload={
                        "board": colorized_board,
                    }
                ), [Message(level=MessagesLevels.INFO.value, text=f"User {command.username} joined!")]

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload=None
                ), [Message(level=MessagesLevels.ERROR.value, text=str(e))]

        elif command.method == CommandMethods.DISCONNECT.value:
            try:
                colorized_board = self._render_board_on_disconnect(command)
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=True,
                    payload={
                        "board": colorized_board,
                    }
                ), [Message(level=MessagesLevels.INFO.value, text=f"User {command.username} disconnected!")]

            except Exception as e:
                return Response(
                    method=ResponseMethods.UPDATE_BOARD.value,
                    success=False,
                    payload={
                        "board": None,
                    }
                ), [Message(level=MessagesLevels.ERROR.value, text=str(e))]

        else:
            raise Exception(f"Command method {command.method} not supported!")
