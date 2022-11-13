import asyncio
import logging
from asyncio import sleep

import numpy as np

from bot.config import *
from data.news import *
from data.statistics import *
from data.subscriptions import *
from data.users import *
from scrolling import lock


def update_statistics():
    for subscription in get_subscription_names():
        posts = get_posts(subscription)
        if len(posts) == 0:
            continue
        reactions_high, reactions_basic = np.percentile([post.reactions for post in posts],
                                                        [PERCENTILE_HIGH, PERCENTILE_BASIC])
        comments_high, comments_basic = np.percentile([post.comments for post in posts],
                                                      [PERCENTILE_HIGH, PERCENTILE_BASIC])
        logging.info(f"Update statistics for channel '{subscription.channel}' "
                     f"#reactions_high={int(reactions_high)}"
                     f"#reactions_basic={int(reactions_basic)}"
                     f"#comments_high={int(comments_high)}"
                     f"#comments_basic={int(comments_basic)}")
        add_statistic(Stat(subscription, reactions_high, reactions_basic, comments_high, comments_basic))
    delete_posts_before(datetime.now() - news_drop_time)


async def notify_user(bot, user_id, start_time=None):
    logging.info(f"Start notification session for {user_id}")
    hard_time_offset = datetime.now() - hard_time_window
    if start_time is None or start_time < hard_time_offset:
        start_time = hard_time_offset
    user_subscriptions = get_subscriptions(user_id)
    chosen_posts = []
    for subscription in user_subscriptions:
        async with lock:
            posts = get_posts(subscription.channel, subscription.last_seen_post)
            posts = [post for post in posts if post.timestamp > start_time]
            if len(posts) == 0:
                continue
            stat = get_statistics(subscription.channel)
            if stat is None:
                logging.warning(f"Cannot notify user, as statistics fot channel {subscription.channel} is not ready")
                continue
            comments, reactions = stat.get_percentiles(subscription.percentile)
            posts = [post for post in posts if post.comments > comments or post.reactions > reactions]
            if len(posts) == 0:
                continue
            last_post_id = posts[-1].post_id
            update_last_seen_post(user_id, subscription.channel, last_post_id)
            chosen_posts += posts
    chosen_posts.sort(key=lambda post: post.timestamp)
    for post in chosen_posts:
        link = f"https://t.me/{post.channel}/{post.post_id}"
        logging.info(f"Send message to {user_id}: {link} #comments={post.comments} #reactions={post.reactions}")
        await bot.send_message(user_id, link)
        await sleep(notification_single_timeout_s)
    return len(chosen_posts)


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
