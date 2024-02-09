import asyncio
import logging
from asyncio import sleep
from collections import defaultdict

import numpy as np
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest
from pyrogram.types import Chat

from bot.config import *
from bot.context import Context
from bot.notify import trigger_notification
from bot.scrolling_utils import app, GetChatStatus, safe_get_channel
from bot.utils import wait_unless_triggered
from storage.posts_storage import PostsStorage, Post, Attachment
from storage.statistic_storage import Statistic, StatisticStorage
from storage.subscriptions_storage import SubscriptionStorage


def trigger_scrolling():
    Context().scrolling_event.set()


def update_statistics():
    PostsStorage.delete_old_posts(datetime.datetime.now() - news_drop_time)
    posts = PostsStorage.get_posts()
    reactions = defaultdict(list)
    comments = defaultdict(list)
    forwards = defaultdict(list)
    for post in posts:
        channel, comment, reaction, forward = post.channel_id, post.comments, post.reactions, post.forwards
        reactions[channel].append(reaction)
        comments[channel].append(comment)
        forwards[channel].append(forward)
    values = []
    for channel in reactions.keys():
        rp = np.percentile(reactions[channel], INTERESTING_PERCENTILES)
        cp = np.percentile(comments[channel], INTERESTING_PERCENTILES)
        fp = np.percentile(forwards[channel], INTERESTING_PERCENTILES)
        for i, p in enumerate(INTERESTING_PERCENTILES):
            values.append(Statistic(channel, p, cp[i], rp[i], fp[i]))
    StatisticStorage.update(values)


async def scheduled_scrolling():
    async with app:
        await sleep(initial_timeout_s)
        while not Context().stop:
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
            await trigger_notification()
            if Context().stop:
                return
            await wait_unless_triggered(scrolling_timeout_s, Context().scrolling_event)


async def collect_chat_history(chat: Chat, channel_id: int, channel_name: str, is_empty: bool):
    hard_time_offset = datetime.datetime.now() - hard_time_window
    soft_time_offset = datetime.datetime.now() - soft_time_window
    posts = []
    has_comments = chat.type != ChatType.CHANNEL or chat.linked_chat is not None
    media_groups = defaultdict(list)

    async for message in app.get_chat_history(chat_id=f"@{channel_name}"):
        if Context().stop:
            return posts

        # ignore service messages
        if message.service is not None:
            continue

        post_id = message.id
        timestamp = message.date
        if timestamp < hard_time_offset or not is_empty and timestamp < soft_time_offset:
            break
        if message.media_group_id is not None:
            media_groups[(channel_id, message.media_group_id)].append(post_id)
        forwards = message.forwards if message.forwards is not None else 0
        reactions = 0
        if message.reactions is not None:
            reactions = sum([reaction.count for reaction in message.reactions.reactions])
        comments = 0
        if has_comments:
            await sleep(scrolling_single_timeout_s)
            try:
                comments = await app.get_discussion_replies_count(f"@{channel_name}", post_id)
            except BadRequest as e:
                if message.media_group_id is not None:
                    continue
                if e.ID == 'MSG_ID_INVALID':
                    # no comments for the post (commercial or something else)
                    pass
                else:
                    logging.warning(f"Failed to update comments in {message.link} {e.MESSAGE}")
        posts.append(Post(channel_id, post_id, comments, reactions, forwards, timestamp))
        await sleep(scrolling_single_timeout_s)

    attachments = []
    for (channel_id, media_group), post_ids in media_groups.items():
        main_post_id = min(post_ids)
        post_ids.remove(main_post_id)
        for post_id in post_ids:
            attachments.append(Attachment(channel_id, main_post_id, post_id))

    return posts, attachments


async def scroll():
    for c in SubscriptionStorage.get_channels():
        await sleep(scrolling_single_timeout_s)
        try:
            channel_name = c.channel
            status, chat = await safe_get_channel(channel_name)
            if status != GetChatStatus.SUCCESS:
                logging.warning(f"Failed to get chat {channel_name}: {status}")
                continue
            posts, attachments = await collect_chat_history(chat, c.id, channel_name, c.is_empty)
            if Context().stop:
                return
            PostsStorage.add_posts(posts)
            PostsStorage.add_attachments(attachments)
            logging.debug(f"Scrolled {len(posts)} posts in {channel_name}")
        except Exception as e:
            logging.exception(e)


def init_scrolling():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_scrolling())
