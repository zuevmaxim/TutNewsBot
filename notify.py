import asyncio
from asyncio import sleep

from config import notification_timeout_s, notification_single_timeout_s
from data.news import *
from data.subscriptions import *
from data.users import *


async def notify_user(bot, user_id):
    user_subscriptions = get_subscriptions(user_id)
    total = 0
    for subscription in user_subscriptions:
        posts = get_popular_posts(subscription.subscription, 3, subscription.last_seen_post)
        if len(posts) == 0:
            continue
        posts.sort(key=lambda post: post.post_id)
        last_post_id = posts[-1].post_id
        update_last_seen_post(user_id, subscription.subscription, last_post_id)
        for post in posts:
            total += 1
            await bot.send_message(user_id, f"https://t.me/{subscription.subscription}/{post.post_id}")
            await sleep(notification_single_timeout_s)
    return total


async def scheduled_notification(bot):
    while True:
        for user in get_users():
            await notify_user(bot, user.user_id)
        await sleep(notification_timeout_s)


def init_notification(bot):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_notification(bot))
