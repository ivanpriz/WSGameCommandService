import random
import uuid
from typing import Iterable


class UserManager:
    def __init__(self, usernames_file: str, colors_file: str):
        self.usernames_file = usernames_file
        self.colors_file = colors_file
        self.conn_id_username_map: dict[uuid.UUID, str] = {}
        self.conn_id_color_map: dict[uuid.UUID, str] = {}

    @staticmethod
    def _get_random_val_from_file(used_vals: Iterable, filepath: str):
        # TODO handle case when running out of vals
        with open(filepath, "r") as f:
            val = None
            file_vals = [l.strip() for l in f.readlines()]
            while not val or val in used_vals:
                val = random.choice(file_vals)

        return val

    @property
    def random_username(self):
        return self._get_random_val_from_file(
            self.conn_id_username_map.values(),
            self.usernames_file,
        )

    @property
    def random_color(self):
        return self._get_random_val_from_file(
            self.conn_id_color_map.values(),
            self.colors_file,
        )

    def create_user(self, conn_id: uuid.UUID) -> tuple[uuid.UUID, str, str]:
        name, color = self.random_username, self.random_color
        self.conn_id_username_map.update({conn_id: name})
        self.conn_id_color_map.update({conn_id: color})
        return conn_id, name, color

    def delete_user(self, conn_id: uuid.UUID):
        self.conn_id_username_map.pop(conn_id)
        self.conn_id_color_map.pop(conn_id)
