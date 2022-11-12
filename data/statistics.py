from datetime import datetime

from pysondb import db

statistics_db = db.getDb("bd/statistics.json")


class Stat:
    def __init__(self, channel, reactions, comments, timestamp=datetime.now()):
        self.channel = channel
        self.reactions = reactions
        self.comments = comments
        self.timestamp = timestamp


def stat_from_json(json):
    time = datetime.fromisoformat(json["timestamp"])
    return Stat(json["channel"], json["reactions"], json["comments"], time)


def add_statistic(stat):
    current = statistics_db.getBy({"channel": stat.channel})
    if len(current) == 0:
        statistics_db.add({"channel": stat.channel,
                           "timestamp": stat.timestamp.isoformat(),
                           "comments": stat.comments,
                           "reactions": stat.reactions})
    else:
        assert len(current) == 1
        current = current[0]
        current["comments"] = stat.comments
        current["reactions"] = stat.reactions
        current["timestamp"] = stat.timestamp.isoformat()
        statistics_db.updateById(current["id"], current)


def get_statistics(channel):
    current = statistics_db.getBy({"channel": channel})
    if len(current) == 0:
        return None
    assert len(current) == 1
    current = current[0]
    return stat_from_json(current)
