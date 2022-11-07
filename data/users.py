from pysondb import db

users_db = db.getDb("bd/users.json")


class User:
    def __init__(self, user_id, name):
        self.user_id = user_id
        self.name = name


def add_user(user):
    current = users_db.getBy({"user_id": user.user_id})
    if len(current) == 0:
        users_db.add({"user_id": user.user_id, "name": user.name})


def get_users():
    return [User(u["user_id"], u["name"]) for u in users_db.getAll()]
