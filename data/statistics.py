from datetime import datetime

from pysondb import db

statistics_db = db.getDb("bd/statistics.json")


class Stat:
    def __init__(self, channel,
                 reactions_high, reactions_basic,
                 comments_high, comments_basic,
                 timestamp=datetime.now()):
        self.channel = channel
        self.reactions_high = reactions_high
        self.reactions_basic = reactions_basic
        self.comments_high = comments_high
        self.comments_basic = comments_basic
        self.timestamp = timestamp


def stat_from_json(json):
    time = datetime.fromisoformat(json["timestamp"])
    return Stat(json["channel"], json["reactions_high"], json["reactions_basic"],
                json["comments_high"], json["comments_basic"], time)


def add_statistic(stat):
    current = statistics_db.getBy({"channel": stat.channel})
    if len(current) == 0:
        statistics_db.add({"channel": stat.channel,
                           "timestamp": stat.timestamp.isoformat(),
                           "comments_high": stat.comments_high,
                           "comments_basic": stat.comments_basic,
                           "reactions_high": stat.reactions_high,
                           "reactions_basic": stat.reactions_basic})
    else:
        assert len(current) == 1
        current = current[0]
        current["comments_high"] = stat.comments_high
        current["comments_basic"] = stat.comments_basic
        current["reactions_high"] = stat.reactions_high
        current["reactions_basic"] = stat.reactions_basic
        current["timestamp"] = stat.timestamp.isoformat()
        statistics_db.updateById(current["id"], current)


def get_statistics(channel):
    current = statistics_db.getBy({"channel": channel})
    if len(current) == 0:
        return None
    assert len(current) == 1
    current = current[0]
    return stat_from_json(current)
