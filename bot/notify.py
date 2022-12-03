import asyncio
import logging
from asyncio import sleep

import numpy as np
from aiogram.types import MessageEntity, MessageEntityType
from pyrogram import types

from bot.config import *
from data.news import *
from data.statistics import *
from data.subscriptions import *
from data.users import *
from scrolling import get_messages, load_file

stop = False
MAX_CAPTION_LENGTH = 900


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
        await sleep(notification_single_timeout_s)
        link = f"https://t.me/{post.channel}/{post.post_id}"
        logging.info(f"Send message to {user_id}: {link} #comments={post.comments} #reactions={post.reactions}")
        if message.text is not None:
            text, entities = create_text(message, message.text)
            await bot.send_message(user_id, text=text, entities=entities,
                                   disable_web_page_preview=True)
            continue
        try:
            if message.photo is not None:
                await resend_file(message.photo.file_id, message, user_id, bot.send_photo)
            elif message.video is not None:
                def send_video(*args, **kwargs):
                    return bot.send_video(*args, **kwargs, width=message.video.width, height=message.video.height)

                await resend_file(message.video.file_id, message, user_id, send_video)
            continue
        except Exception as e:
            logging.exception(e)
        await bot.send_message(user_id, parse_mode="markdown", text=f"[{message.chat.title}]({link})")

    return len(chosen_posts)


async def resend_file(file_id, message, user_id, send):
    file = await load_file(file_id)
    text = message.caption if message.caption is not None else ""
    if len(text) > MAX_CAPTION_LENGTH:
        text = text[:MAX_CAPTION_LENGTH] + "..."
    text, entities = create_text(message, text)
    try:
        with open(file, "rb") as f:
            await send(user_id, f, caption=text, caption_entities=entities)
    finally:
        os.remove(file)


def create_text(message: types.Message, text: str):
    entities = message.entities if message.entities is not None else []

    # repack entities from pyrogram to aiogram
    entities = [MessageEntity(e.type.name.lower(), e.offset, e.length, e.url, e.user, e.language, e.custom_emoji_id) for e in entities]

    # cut entities in case text is cut
    entities = [e for e in entities if e.offset < len(text)]
    for e in entities:
        if e.offset + e.length > len(text):
            e.length = len(text) - e.offset

    # add chat name in the beginning
    chat_name = f"{message.chat.title}:\n"
    text = chat_name + text
    for e in entities:
        e.offset += len(chat_name)
    entities = [MessageEntity(type=MessageEntityType.BOLD, offset=0, length=len(chat_name))] + entities

    # add link in the end
    link = f"\n{message.chat.username}"
    entities.append(MessageEntity(MessageEntityType.TEXT_LINK, offset=len(text), length=len(link), url=message.link))
    text += link
    return text, entities


async def scheduled_statistics():
    await sleep(initial_timeout_s)
    while True:
        try:
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
