import asyncio
import logging
from asyncio import sleep

from pyrogram import Client
from pyrogram.errors import BadRequest

from bot.config import *
from data.news import *
from data.subscriptions import *

app = Client("scroller", api_id=api_id, api_hash=api_hash)

stop = False


def stop_scrolling():
    global stop
    stop = True


async def get_channel(channel):
    return await app.get_chat(chat_id=f"@{channel}")


async def get_messages(channel, post_ids):
    return await app.get_messages(chat_id=f"@{channel}", message_ids=post_ids)


async def load_file(file_id):
    return await app.download_media(file_id)


async def scheduled_scrolling():
    first_scroll = True
    async with app:
        await sleep(initial_timeout_s)
        while True:
            try:
                await scroll(first_scroll)
                first_scroll = False
            except Exception as e:
                logging.exception(e)
            if stop:
                return
            await sleep(scrolling_timeout_s)


async def scroll(first_scroll):
    for subscription in get_subscription_names():
        # do not scroll messages earlier than one hour
        soft_time_offset = datetime.datetime.now() - soft_time_window
        hard_time_offset = datetime.datetime.now() - hard_time_window

        chat = await get_channel(subscription)
        has_comments = chat.linked_chat is not None
        async for message in app.get_chat_history(chat_id=f"@{subscription}"):
            if stop:
                return
            post_id = message.id
            timestamp = message.date
            if timestamp < hard_time_offset:
                break
            if not first_scroll and timestamp < soft_time_offset and has_post(subscription, post_id):
                break
            reactions = 0
            if message.reactions is not None:
                reactions = sum([reaction.count for reaction in message.reactions.reactions])
            comments = 0
            if has_comments:
                await sleep(scrolling_single_timeout_s)
                try:
                    comments = await app.get_discussion_replies_count(f"@{subscription}", post_id)
                except BadRequest as e:
                    if message.media_group_id is not None:
                        continue
                    logging.warning(f"Failed to update comments in {message.link} {e.MESSAGE}")
            add_post(Post(subscription, post_id, timestamp, comments, reactions))
            logging.info(f"Update channel {subscription} post {post_id}, "
                         f"#comments={comments}, "
                         f"#reactions={reactions}")
            await sleep(scrolling_single_timeout_s)


def init_scrolling():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_scrolling())
