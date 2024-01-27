from dataclasses import dataclass
from datetime import datetime
from typing import List, Optional

from dacite import from_dict

from storage.postgres import db


@dataclass(frozen=True)
class PostNotification:
    post_id: int
    channel: str
    user_id: int
    extra_post_id: Optional[int] = None

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=PostNotification, data=json_data)


@dataclass(frozen=True)
class Post:
    channel_id: int
    post_id: int
    comments: int
    reactions: int
    forwards: int
    timestamp: datetime

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=Post, data=json_data)


@dataclass(frozen=True)
class Attachment:
    channel_id: int
    main_post_id: int
    post_id: int


@dataclass(frozen=True)
class PostStatistics:
    channel_id: int
    comments: int
    reactions: int
    forwards: int

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=PostStatistics, data=json_data)


class PostsStorage:
    @staticmethod
    def get_notification_posts(hard_time_offset: datetime) -> List[PostNotification]:
        cursor = db.execute(
            "SELECT Channel.name AS channel, Post.post_id, BotUser.user_id, Attachment.post_id AS extra_post_id "
            "FROM Subscription "
            "JOIN Channel ON Subscription.channel_id = Channel.id "
            "JOIN BotUser ON BotUser.id = Subscription.user_id "
            "JOIN Post ON Channel.id = Post.channel_id "
            "LEFT JOIN Attachment ON Post.id = Attachment.main_post_id "
            "INNER JOIN Statistics ON Channel.id = Statistics.channel_id "
            "  AND Statistics.percentile = Subscription.percentile "
            "WHERE Post.post_id > Subscription.last_seen_post_id "
            "AND Post.timestamp >= %s "
            "AND (Post.comments > Statistics.comments "
            "OR Post.reactions > Statistics.reactions "
            "OR (Post.reactions = 0 AND Post.comments = 0 AND Post.forwards > Statistics.forwards) )"
            "ORDER BY Post.timestamp",
            [hard_time_offset])
        return list(map(PostNotification.parse_json, cursor))

    @staticmethod
    def get_posts() -> List[PostStatistics]:
        cursor = db.execute("SELECT Post.channel_id, Post.comments, Post.reactions, Post.forwards FROM Post")
        return list(map(PostStatistics.parse_json, cursor))

    @staticmethod
    def add_posts(posts: List[Post]):
        if len(posts) == 0:
            return
        str_args = ", ".join(["(%s, %s, %s, %s, %s, %s)"] * len(posts))
        args = []
        for post in posts:
            args += [post.post_id, post.channel_id, post.timestamp, post.comments, post.reactions, post.forwards]
        db.execute("INSERT INTO Post(post_id, channel_id, timestamp, comments, reactions, forwards) "
                   "VALUES {} ON CONFLICT (post_id, channel_id) DO UPDATE SET "
                   "comments = excluded.comments, "
                   "reactions = excluded.reactions, "
                   "forwards = excluded.forwards, "
                   "timestamp = excluded.timestamp".format(str_args), args)

    @staticmethod
    def add_attachments(attachments: List[Attachment]):
        if len(attachments) == 0:
            return
        str_args = ", ".join(["(%s, %s, %s)"] * len(attachments))
        args = []
        for attachment in attachments:
            args += [attachment.channel_id, attachment.main_post_id, attachment.post_id]
        db.execute("WITH A (channel_id, main_post_id, post_id) AS (VALUES {}) "
                   "INSERT INTO Attachment(post_id, main_post_id) "
                   "SELECT A.post_id, Post.id "
                   "FROM A "
                   "INNER JOIN Post "
                   "ON A.channel_id = Post.channel_id "
                   "AND A.main_post_id = Post.post_id "
                   "ON CONFLICT DO NOTHING".format(str_args), args)

    @staticmethod
    def delete_old_posts(time_offset):
        db.execute("DELETE FROM Attachment "
                   "USING Post "
                   "WHERE Attachment.main_post_id = Post.id "
                   "AND timestamp <= %s; "
                   "DELETE FROM Post WHERE timestamp <= %s", [time_offset, time_offset])
