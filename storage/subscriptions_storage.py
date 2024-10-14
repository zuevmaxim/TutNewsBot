from dataclasses import dataclass
from typing import List, Optional

from dacite import from_dict

from storage.postgres import db


@dataclass(frozen=True)
class Subscription:
    user_id: int
    channel: str
    percentile: int

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=Subscription, data=json_data)


@dataclass(frozen=True)
class Channel:
    id: int
    channel: str
    is_empty: bool
    last_seen_post_id: int

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=Channel, data=json_data)


class SubscriptionStorage:
    @staticmethod
    def get_subscription_names(user_id) -> List[str]:
        cursor = db.execute("SELECT Channel.name "
                            "FROM Subscription "
                            "JOIN Channel ON Channel.id = Subscription.channel_id "
                            "JOIN BotUser ON BotUser.id = Subscription.user_id "
                            "WHERE BotUser.user_id = %s", [user_id])
        return [row[0] for row in cursor]

    @staticmethod
    def get_channels() -> List[Channel]:
        cursor = db.execute(
            "SELECT DISTINCT Channel.id, Channel.name AS channel, MIN(post.post_id) IS NULL as is_empty, Channel.last_seen_post_id "
            "FROM Subscription "
            "JOIN Channel ON Channel.id = Subscription.channel_id "
            "LEFT JOIN Post ON Channel.id = Post.channel_id "
            "GROUP BY Channel.id, Channel.name")
        return list(map(Channel.parse_json, cursor))

    @staticmethod
    def update_last_seen_post_id(channel_id: int, post_id: int):
        db.execute("UPDATE Channel SET last_seen_post_id = %s WHERE id = %s",
                   [post_id, channel_id])

    @staticmethod
    def get_subscription(user_id: str, channel: str) -> Optional[Subscription]:
        cursor = db.execute("SELECT BotUser.user_id, Channel.name AS channel, Subscription.percentile "
                            "FROM Subscription "
                            "JOIN Channel ON Channel.id = Subscription.channel_id "
                            "JOIN BotUser ON BotUser.id = Subscription.user_id "
                            "WHERE BotUser.user_id = %s "
                            "AND Channel.name = %s", (user_id, channel))
        result = list(cursor)
        assert len(result) <= 1
        if len(result) == 0:
            return None
        return Subscription.parse_json(result[0])

    @staticmethod
    def add_subscription(subscription: Subscription):
        db.execute("INSERT INTO Channel (name) "
                   "VALUES (%s) "
                   "ON CONFLICT (name) DO NOTHING", [subscription.channel])
        db.execute("INSERT INTO Subscription(user_id, channel_id, percentile) "
                   "VALUES ("
                   "(SELECT BotUser.id FROM BotUser WHERE BotUser.user_id = %s), "
                   "(SELECT Channel.id FROM Channel WHERE Channel.name = %s), "
                   "%s) "
                   "ON CONFLICT (user_id, channel_id) DO UPDATE "
                   "SET percentile = excluded.percentile",
                   (subscription.user_id, subscription.channel, subscription.percentile))

    @staticmethod
    def remove_subscription(user_id: str, channel_id):
        db.execute("DELETE FROM Subscription "
                   "WHERE user_id = (SELECT id FROM BotUser WHERE user_id = %s) "
                   "AND channel_id = (SELECT id FROM Channel WHERE name = %s)",
                   (user_id, channel_id))

    @staticmethod
    def update(max_ids):
        for channel, user_id, post_id in max_ids:
            db.execute("UPDATE Subscription "
                       "SET last_seen_post_id = %s "
                       "WHERE channel_id = (SELECT id FROM Channel WHERE name = %s) "
                       "AND user_id = (SELECT id FROM BotUser WHERE user_id = %s)",
                       [post_id, channel, user_id])
