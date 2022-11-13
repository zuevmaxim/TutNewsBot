from data.news import news_db
from data.statistics import statistics_db
from data.subscriptions import subscriptions_db
from data.users import users_db


def close_db():
    with news_db.lock.acquire():
        pass
    with statistics_db.lock.acquire():
        pass
    with subscriptions_db.lock.acquire():
        pass
    with users_db.lock.acquire():
        pass
