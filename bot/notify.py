import asyncio
import logging
import shutil
from asyncio import sleep
from collections import defaultdict
from typing import List

from aiogram.types import MessageEntity, MessageEntityType
from aiogram.utils.exceptions import BotBlocked
from pyrogram import types
from pyrogram.enums import ChatType

from bot.config import *
from scrolling import get_messages, load_file
from storage.posts_storage import PostsStorage, PostNotification
from storage.subscriptions_storage import SubscriptionStorage

stop = False
MAX_CAPTION_LENGTH = 900


def stop_notifications():
    global stop
    stop = True


def update_seen_posts(posts: List[PostNotification]):
    res = defaultdict(list)
    for post in posts:
        res[(post.channel, post.user_id)].append(post.post_id)
    max_ids = [(channel, user_id, max(post_ids)) for (channel, user_id), post_ids in res.items()]
    SubscriptionStorage.update(max_ids)


async def notify(bot):
    clear_cache_dir()
    hard_time_offset = datetime.datetime.now() - hard_time_window
    posts = PostsStorage.get_notification_posts(hard_time_offset)
    if len(posts) == 0:
        return
    logging.info("Start notification session")
    res = defaultdict(set)
    for post in posts:
        res[post.channel].add(post.post_id)
    loaded = {}
    for channel, post_ids in res.items():
        try:
            post_ids = list(post_ids)
            messages = await get_messages(channel, post_ids)
            for post_id, message in zip(post_ids, messages):
                loaded[(channel, post_id)] = message
        except Exception as e:
            logging.exception(e)
    update_seen_posts(posts)
    file_cache = {}
    disabled_users = set()
    for post in posts:
        user_id = post.user_id
        if user_id in disabled_users:
            continue
        await sleep(notification_single_timeout_s)
        message = loaded[(post.channel, post.post_id)]
        try:
            await send_message(bot, user_id, message, file_cache)
        except BotBlocked:
            logging.info(f"User {user_id} blocked the bot. Disable for this notification.")
            disabled_users.add(user_id)
        except Exception as e:
            logging.exception(e)
    for file in file_cache.values():
        os.remove(file)
    clear_cache_dir()


def clear_cache_dir():
    shutil.rmtree("bot/downloads", ignore_errors=True)


async def send_message(bot, user_id, message, file_cache):
    logging.info(f"Send message to {user_id}: {message.link}")
    try:
        if message.text is not None:
            text, entities = create_text(message, message.text)
            await bot.send_message(user_id, text=text, entities=entities,
                                   disable_web_page_preview=True)
            return
        if message.photo is not None:
            await resend_file(message.photo.file_id, message, user_id, bot.send_photo, file_cache)
            return
        elif message.video is not None and message.video.file_size < 5 * 10 ** 7:
            def send_video(*args, **kwargs):
                return bot.send_video(*args, **kwargs, width=message.video.width, height=message.video.height)

            await resend_file(message.video.file_id, message, user_id, send_video, file_cache)
            return
    except BotBlocked as e:
        raise e
    except Exception as e:
        logging.exception(e)
    await bot.send_message(user_id, parse_mode="markdown", text=f"[{message.chat.title}]({message.link})")


async def resend_file(file_id: str, message: types.Message, user_id: int, send, file_cache):
    if file_id in file_cache:
        file = file_cache[file_id]
    else:
        file = await load_file(file_id)
        file_cache[file_id] = file
    text = message.caption if message.caption is not None else ""
    if len(text) > MAX_CAPTION_LENGTH:
        text = text[:MAX_CAPTION_LENGTH] + "..."
    text, entities = create_text(message, text)
    with open(file, "rb") as f:
        await send(user_id, f, caption=text, caption_entities=entities)


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
    if message.chat.type == ChatType.CHANNEL:
        chat_name = f"{message.chat.title}:\n"
    else:
        author = f"{message.from_user.first_name} {message.from_user.last_name}"
        chat_name = f"{message.chat.title} ({author}):\n"

    text = chat_name + text
    for e in entities:
        e.offset += len(chat_name)
    entities = [MessageEntity(type=MessageEntityType.BOLD, offset=0, length=len(chat_name))] + entities

    # add link in the end
    link = f"\n{message.chat.username}"
    entities.append(MessageEntity(MessageEntityType.TEXT_LINK, offset=len(text), length=len(link), url=message.link))
    text += link
    return text, entities


async def scheduled_notification(bot):
    await sleep(initial_timeout_s)
    while True:
        if stop:
            return
        try:
            await notify(bot)
        except Exception as e:
            logging.exception(e)
        if stop:
            return
        await sleep(notification_timeout_s)


def init_notification(bot):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_notification(bot))
