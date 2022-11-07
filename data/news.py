import datetime

from pysondb import db

news_db = db.getDb("bd/news.json")


class Post:
    def __init__(self, chanel, post_id, timestamp, comments, reactions):
        self.chanel = chanel
        self.post_id = post_id
        self.timestamp = timestamp
        self.comments = comments
        self.reactions = reactions


def post_from_json(json):
    time = datetime.datetime.fromisoformat(json["timestamp"])
    return Post(json["channel"], json["post_id"], time, json["comments"], json["reactions"])


def add_post(post):
    current = news_db.getBy({"channel": post.chanel, "post_id": post.post_id})
    if len(current) == 0:
        news_db.add({"channel": post.chanel,
                     "post_id": post.post_id,
                     "timestamp": post.timestamp.isoformat(),
                     "comments": post.comments,
                     "reactions": post.reactions})
    else:
        assert len(current) == 1
        current = current[0]
        current["comments"] = post.comments
        current["reactions"] = post.reactions
        news_db.updateById(current["id"], current)


def has_post(chanel, post_id):
    current = news_db.getBy({"channel": chanel, "post_id": post_id})
    return len(current) > 0


def get_popular_posts(chanel, count, last_seen_post):
    current = news_db.getBy({"channel": chanel})
    current = list(map(post_from_json, current))
    current = [post for post in current if post.post_id > last_seen_post]
    current = list(sorted(current, key=lambda post: post.comments + post.reactions))
    return current[-count:]


def delete_posts_before(date):
    outdated = [o["id"] for o in news_db.getAll() if datetime.datetime.fromisoformat(o["timestamp"]) < date]
    for id in outdated:
        news_db.deleteById(id)
