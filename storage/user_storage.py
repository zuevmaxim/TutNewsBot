from dataclasses import dataclass
from typing import List

from dacite import from_dict

from storage.postgres import db


@dataclass(frozen=True)
class User:
    user_id: int
    lang: str

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=User, data=json_data)


class UserStorage:
    @staticmethod
    def get_users() -> List[User]:
        cursor = db.execute("SELECT user_id, lang FROM BotUser")
        return [User.parse_json(row) for row in cursor]

    @staticmethod
    def add_user(user: User):
        db.execute("INSERT INTO BotUser (user_id, lang) "
                   "VALUES (%s, %s) "
                   "ON CONFLICT (user_id) DO UPDATE "
                   "SET lang = excluded.lang", (user.user_id, user.lang))
