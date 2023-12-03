import asyncio
import logging
from asyncio import sleep
from collections import defaultdict
from enum import Enum
from typing import List

import numpy as np
from pyrogram import Client, types
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest
from pyrogram.types import Chat

from bot.config import *
from storage.posts_storage import PostsStorage, Post
from storage.statistic_storage import Statistic, StatisticStorage
from storage.subscriptions_storage import SubscriptionStorage

app = Client("scroller", api_id=api_id, api_hash=api_hash)

stop = False


def stop_scrolling():
    global stop
    stop = True


class GetChatStatus(Enum):
    SUCCESS = "success"
    USER_NOT_EXIST = "user does not exist"
    PRIVATE_CHAT = "chat is private"


async def safe_get_channel(channel: str):
    try:
        chat = await app.get_chat(chat_id=f"@{channel}")
        public_chat = (chat.type == ChatType.CHANNEL or
                       chat.type == ChatType.GROUP or
                       chat.type == ChatType.SUPERGROUP) and chat.username is not None
        if not public_chat or chat.type == ChatType.PRIVATE or chat.type == ChatType.BOT:
            return GetChatStatus.PRIVATE_CHAT, chat
        return GetChatStatus.SUCCESS, chat
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID" or e.ID == "USERNAME_NOT_OCCUPIED":
            return GetChatStatus.USER_NOT_EXIST, None
        raise e


async def get_messages(channel: str, post_ids: List[int]) -> List[types.Message]:
    return await app.get_messages(chat_id=f"@{channel}", message_ids=post_ids)


async def load_file(file_id: str) -> str:
    return await app.download_media(file_id)


def update_statistics():
    posts = PostsStorage.get_posts()
    reactions = defaultdict(list)
    comments = defaultdict(list)
    for post in posts:
        channel, comment, reaction = post.channel_id, post.comments, post.reactions
        reactions[channel].append(reaction)
        comments[channel].append(comment)
    values = []
    for channel in reactions.keys():
        rp = np.percentile(reactions[channel], INTERESTING_PERCENTILES)
        cp = np.percentile(comments[channel], INTERESTING_PERCENTILES)
        for i, p in enumerate(INTERESTING_PERCENTILES):
            values.append(Statistic(channel, p, cp[i], rp[i]))
    StatisticStorage.update(values)
    PostsStorage.delete_old_posts(datetime.datetime.now() - news_drop_time)


async def scheduled_scrolling():
    async with app:
        await sleep(initial_timeout_s)
        while True:
            logging.info("Start scrolling session")
            try:
                await scroll()
            except Exception as e:
                logging.exception(e)
            try:
                update_statistics()
            except Exception as e:
                logging.exception(e)
            logging.info("Complete scrolling session")
            if stop:
                return
            await sleep(scrolling_timeout_s)

async def collect_chat_history(chat: Chat, channel_id: int, channel: str, is_empty: bool):
    hard_time_offset = datetime.datetime.now() - hard_time_window
    soft_time_offset = datetime.datetime.now() - soft_time_window
    posts = []
    has_comments = chat.type != ChatType.CHANNEL or chat.linked_chat is not None
    async for message in app.get_chat_history(chat_id=f"@{channel}"):
        if stop:
            return posts

        # ignore service messages
        if message.service is not None:
            continue

        post_id = message.id
        timestamp = message.date
        if timestamp < hard_time_offset or not is_empty and timestamp < soft_time_offset:
            break
        reactions = 0
        if message.reactions is not None:
            reactions = sum([reaction.count for reaction in message.reactions.reactions])
        comments = 0
        if has_comments:
            await sleep(scrolling_single_timeout_s)
            try:
                comments = await app.get_discussion_replies_count(f"@{channel}", post_id)
            except BadRequest as e:
                if message.media_group_id is not None:
                    continue
                if e.ID == 'MSG_ID_INVALID':
                    # no comments for the post (commercial or something else)
                    pass
                else:
                    logging.warning(f"Failed to update comments in {message.link} {e.MESSAGE}")
        posts.append(Post(channel_id, post_id, comments, reactions, timestamp))
        await sleep(scrolling_single_timeout_s)
    return posts


async def scroll():
    for c in SubscriptionStorage.get_channels():
        try:
            channel = c.channel
            status, chat = await safe_get_channel(channel)
            if status != GetChatStatus.SUCCESS:
                logging.warning(f"Failed to get chat {channel}: {status}")
                continue
            posts = await collect_chat_history(chat, c.id, channel, c.is_empty)
            if stop:
                return
            PostsStorage.add_posts(posts)
            logging.info(f"Scrolled {len(posts)} posts in {channel}")
        except Exception as e:
            logging.exception(e)


def init_scrolling():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_scrolling())
