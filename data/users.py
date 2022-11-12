from pysondb import db

users_db = db.getDb("bd/users.json")


class User:
    def __init__(self, user_id, name, lang):
        self.user_id = user_id
        self.name = name
        self.lang = lang


def add_user(user):
    current = users_db.getBy({"user_id": user.user_id})
    if len(current) == 0:
        users_db.add({"user_id": user.user_id, "name": user.name, "lang": user.lang})
    else:
        assert len(current) == 1
        current = current[0]
        current["name"] = user.name
        current["lang"] = user.lang
        users_db.updateById(current["id"], current)


def get_users():
    return [User(u["user_id"], u["name"], u["lang"]) for u in users_db.getAll()]
