import asyncio
import logging
from asyncio import sleep
from collections import defaultdict
from typing import List

import numpy as np
from pyrogram import Client, types
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from bot.config import *
from storage.posts_storage import PostsStorage, Post
from storage.statistic_storage import Statistic, StatisticStorage
from storage.subscriptions_storage import SubscriptionStorage

app = Client("scroller", api_id=api_id, api_hash=api_hash)

stop = False


def stop_scrolling():
    global stop
    stop = True


async def get_channel(channel: str):
    return await app.get_chat(chat_id=f"@{channel}")


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
        first_run = True
        while True:
            try:
                await scroll(first_run)
                first_run = False
            except Exception as e:
                logging.exception(e)
            try:
                update_statistics()
            except Exception as e:
                logging.exception(e)
            if stop:
                return
            await sleep(scrolling_timeout_s)


async def scroll(first_run: bool):
    logging.info("Start scrolling session")
    posts = []
    for c in SubscriptionStorage.get_channels():
        channel_id, channel = c.id, c.channel
        hard_time_offset = datetime.datetime.now() - hard_time_window
        soft_time_offset = datetime.datetime.now() - soft_time_window

        chat = await get_channel(channel)
        has_comments = chat.type != ChatType.CHANNEL or chat.linked_chat is not None
        async for message in app.get_chat_history(chat_id=f"@{channel}"):
            if stop:
                return

            # ignore service messages
            if message.service is not None:
                continue

            post_id = message.id
            timestamp = message.date
            if timestamp < hard_time_offset or not first_run and timestamp < soft_time_offset :
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
                    logging.warning(f"Failed to update comments in {message.link} {e.MESSAGE}")
            posts.append(Post(channel_id, post_id, comments, reactions, timestamp))
            await sleep(scrolling_single_timeout_s)
        PostsStorage.add_posts(posts)
        posts = []


def init_scrolling():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_scrolling())
