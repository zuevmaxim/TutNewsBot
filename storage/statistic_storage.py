from dataclasses import dataclass
from typing import List

from dacite import from_dict

from storage.postgres import db


@dataclass(frozen=True)
class Statistic:
    channel: int
    percentile: int
    comments: int
    reactions: int

    @staticmethod
    def parse_json(json_data: dict):
        return from_dict(data_class=Statistic, data=json_data)


class StatisticStorage:
    @staticmethod
    def update(values: List[Statistic]):
        if len(values) == 0:
            return
        str_args = ", ".join(["(%s, %s, %s, %s)"] * len(values))
        args = []
        for s in values:
            args += [s.channel, s.percentile, s.comments, s.reactions]
        db.execute("INSERT INTO Statistics (channel_id, percentile, comments, reactions) "
                   "VALUES {} "
                   "ON CONFLICT (channel_id, percentile) DO UPDATE SET "
                   "comments = excluded.comments, "
                   "reactions = excluded.reactions".format(str_args), args)
