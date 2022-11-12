import asyncio
import logging
from asyncio import sleep

import numpy as np

from config import *
from data.news import *
from data.statistics import *
from data.subscriptions import *
from data.users import *
from scrolling import lock


def update_statistics():
    for subscription in get_subscription_names():
        posts = get_posts(subscription)
        reactions = np.percentile([post.reactions for post in posts], reactions_percentile)
        comments = np.percentile([post.comments for post in posts], comments_percentile)
        add_statistic(Stat(subscription, reactions, comments))
    delete_posts_before(datetime.now() - news_drop_time)


async def notify_user(bot, user_id, start_time=None):
    async with lock:
        user_subscriptions = get_subscriptions(user_id)
        total = 0
        for subscription in user_subscriptions:
            posts = get_posts(subscription.channel, subscription.last_seen_post)
            if start_time is not None:
                posts = [post for post in posts if post.timestamp > start_time]
            if len(posts) == 0:
                continue
            stat = get_statistics(subscription.channel)
            posts = [post for post in posts if post.comments > stat.comments or post.reactions > stat.reactions]
            if len(posts) == 0:
                continue
            last_post_id = posts[-1].post_id
            update_last_seen_post(user_id, subscription.channel, last_post_id)
            for post in posts:
                total += 1
                link = f"https://t.me/{subscription.channel}/{post.post_id}"
                logging.info(f"Send message to {user_id}: {link} #comments={post.comments} #reactions={post.reactions}")
                await bot.send_message(user_id, link)
                await sleep(notification_single_timeout_s)
    return total


async def scheduled_statistics():
    await sleep(initial_timeout_s)
    while True:
        async with lock:
            update_statistics()
        await sleep(statistics_update_s)


async def scheduled_notification(bot):
    start_time = datetime.now()
    await sleep(initial_timeout_s)
    while True:
        for user in get_users():
            await notify_user(bot, user.user_id, start_time)
        await sleep(notification_timeout_s)


def init_notification(bot):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_statistics())
    loop.create_task(scheduled_notification(bot))
