import asyncio
import logging
from asyncio import sleep

import numpy as np
from pyrogram.enums import MessageEntityType

from bot.config import *
from data.news import *
from data.statistics import *
from data.subscriptions import *
from data.users import *
from scrolling import lock, get_messages

stop = False


def stop_notifications():
    global stop
    stop = True


def update_statistics():
    for channel in get_subscription_names():
        if stop:
            return
        posts = get_posts(channel)
        if len(posts) == 0:
            continue
        reactions_high, reactions_basic = np.percentile([post.reactions for post in posts],
                                                        [PERCENTILE_HIGH, PERCENTILE_BASIC])
        comments_high, comments_basic = np.percentile([post.comments for post in posts],
                                                      [PERCENTILE_HIGH, PERCENTILE_BASIC])
        logging.info(f"Update statistics for channel '{channel}' "
                     f"#reactions_high={int(reactions_high)}"
                     f"#reactions_basic={int(reactions_basic)}"
                     f"#comments_high={int(comments_high)}"
                     f"#comments_basic={int(comments_basic)}")
        add_statistic(Stat(channel, reactions_high, reactions_basic, comments_high, comments_basic))
    delete_posts_before(datetime.now() - news_drop_time)


async def notify_user(bot, user_id):
    logging.info(f"Start notification session for {user_id}")
    hard_time_offset = datetime.now() - hard_time_window
    user_subscriptions = get_subscriptions(user_id)
    chosen_posts = []
    for subscription in user_subscriptions:
        async with lock:
            posts = get_posts(subscription.channel, subscription.last_seen_post)
            posts = [post for post in posts if post.timestamp > hard_time_offset]
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
            posts = list(zip(posts, await get_messages(subscription.channel, [post.post_id for post in posts])))
            chosen_posts += posts
    chosen_posts.sort(key=lambda post: post[0].timestamp)
    for post, message in chosen_posts:
        link = f"https://t.me/{post.channel}/{post.post_id}"
        logging.info(f"Send message to {user_id}: {link} #comments={post.comments} #reactions={post.reactions}")
        if message.text is not None:
            text = to_markdown(message.text, message.entities)
            await bot.send_message(user_id, parse_mode="markdown",
                                   text=f"*{message.chat.title}*\n{text}\n[{post.channel}]({link})",
                                   disable_web_page_preview=True)
        else:
            await bot.send_message(user_id, parse_mode="markdown", text=f"[{message.chat.title}]({link})")
        await sleep(notification_single_timeout_s)
    return len(chosen_posts)


def to_markdown(text, entities):
    if entities is None or len(entities) == 0:
        return text
    new_text = text[:entities[0].offset]
    for i, e in enumerate(entities):
        if e.type == MessageEntityType.BOLD:
            c = '*'
        elif e.type == MessageEntityType.ITALIC:
            c = '_'
        else:
            c = ''
        new_text += c + text[e.offset: e.offset + e.length] + c
        if i + 1 == len(entities):
            new_text += text[e.offset + e.length:]
        else:
            new_text += text[e.offset + e.length: entities[i + 1].offset]
    return new_text


async def scheduled_statistics():
    await sleep(initial_timeout_s)
    while True:
        try:
            async with lock:
                update_statistics()
        except Exception as e:
            logging.exception(e)
        if stop:
            return
        await sleep(statistics_update_s)


async def scheduled_notification(bot):
    await sleep(initial_timeout_s)
    while True:
        try:
            for user in get_users():
                if stop:
                    return
                await notify_user(bot, user.user_id)
        except Exception as e:
            logging.exception(e)
        if stop:
            return
        await sleep(notification_timeout_s)


def init_notification(bot):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_statistics())
    loop.create_task(scheduled_notification(bot))
