import asyncio
import logging
from asyncio import sleep

from pyrogram import Client
from pyrogram.errors import BadRequest

from config import *
from data.news import *
from data.subscriptions import *

app = Client("scroller", api_id=api_id, api_hash=api_hash)

lock = asyncio.Lock()

async def scheduled_scrolling():
    async with app:
        while True:
            async with lock:
                interesting_subscriptions = set()
                for subscription in get_subscription_names():
                    interesting_subscriptions.add(subscription)

                # do not scroll messages earlier than one hour
                soft_time_offset = datetime.datetime.now() - soft_time_window
                hard_time_offset = datetime.datetime.now() - hard_time_window
                for subscription in interesting_subscriptions:
                    chat = await app.get_chat(chat_id=f"@{subscription}")
                    has_comments = chat.linked_chat is not None
                    async for message in app.get_chat_history(chat_id=f"@{subscription}"):
                        post_id = message.id
                        timestamp = message.date
                        if timestamp < hard_time_offset:
                            break
                        if timestamp < soft_time_offset and has_post(subscription, post_id):
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
                        logging.info(f"Update chanel {subscription} post {post_id}, "
                                     f"#comments={comments}, "
                                     f"#reactions={reactions}")
                        await sleep(scrolling_single_timeout_s)

                delete_posts_before(hard_time_offset)
            await sleep(scrolling_timeout_s)


def init_scrolling():
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_scrolling())
