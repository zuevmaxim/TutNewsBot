from pysondb import db

subscriptions_db = db.getDb("bd/subscriptions.json")


class Subscription:
    def __init__(self, user_id, channel, percentile, last_seen_post=-1):
        self.user_id = user_id
        self.channel = channel
        self.percentile = percentile
        self.last_seen_post = last_seen_post


def subscription_from_json(json):
    return Subscription(json["user_id"], json["channel"], json["percentile"], json["last_seen_post"])


def add_subscription(subscription):
    current = subscriptions_db.getBy({"user_id": subscription.user_id, "channel": subscription.channel})
    if len(current) == 0:
        subscriptions_db.add({"user_id": subscription.user_id, "channel": subscription.channel,
                              "percentile": subscription.percentile, "last_seen_post": subscription.last_seen_post})
    else:
        assert len(current) == 1
        current = current[0]
        current["percentile"] = subscription.percentile
        subscriptions_db.updateById(current["id"], current)


def remove_subscription(user_id, channel):
    current = subscriptions_db.getBy({"user_id": user_id, "channel": channel})
    if len(current) > 0:
        assert len(current) == 1
        current = current[0]
        subscriptions_db.deleteById(current["id"])
        return True
    return False


def get_subscription_names(user_id=None):
    current = subscriptions_db.getAll() if user_id is None else \
        subscriptions_db.getBy({"user_id": user_id})
    return set([e["channel"] for e in current])


def get_subscriptions(user_id=None):
    current = subscriptions_db.getAll() if user_id is None else \
        subscriptions_db.getBy({"user_id": user_id})
    return list(map(subscription_from_json, current))


def get_subscription(user_id, channel):
    current = subscriptions_db.getBy({"user_id": user_id, "channel": channel})
    if len(current) == 0:
        return None
    assert len(current) == 1
    return subscription_from_json(current[0])


def update_last_seen_post(user_id, channel, last_post):
    current = subscriptions_db.getBy({"user_id": user_id, "channel": channel})
    if len(current) == 1:
        current = current[0]
        current["last_seen_post"] = last_post
        subscriptions_db.updateById(current["id"], current)
