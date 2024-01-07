import asyncio
import logging
import shutil
from asyncio import sleep
from collections import defaultdict
from typing import List, Tuple, Dict, Optional

from aiogram.enums import MessageEntityType
from aiogram.exceptions import TelegramForbiddenError
from aiogram.types import MessageEntity, FSInputFile
from aiogram.utils.media_group import MediaGroupBuilder
from pyrogram import types
from pyrogram.enums import ChatType

from bot.config import *
from bot.context import Context
from bot.scrolling_utils import get_messages, load_file
from bot.utils import wait_unless_triggered
from storage.posts_storage import PostsStorage, PostNotification
from storage.subscriptions_storage import SubscriptionStorage

MAX_CAPTION_LENGTH = 900


def trigger_notification():
    Context().notification_event.set()


def update_seen_posts(posts: List[PostNotification]):
    res = defaultdict(list)
    for post in posts:
        res[(post.channel, post.user_id)].append(post.post_id)
    max_ids = [(channel, user_id, max(post_ids)) for (channel, user_id), post_ids in res.items()]
    SubscriptionStorage.update(max_ids)


def filter_original_posts(posts: List[PostNotification]) -> \
        Tuple[List[PostNotification], Dict[PostNotification, List[int]]]:
    attachments = defaultdict(list)
    original_posts = []
    for post in posts:
        original_post = PostNotification(post.post_id, post.channel, post.user_id)
        has_attachment = post.extra_post_id is not None
        if not has_attachment or original_post not in attachments:
            original_posts.append(original_post)
        if has_attachment:
            attachments[original_post].append(post.extra_post_id)
    return original_posts, attachments


async def notify(bot):
    clear_cache_dir()
    hard_time_offset = datetime.datetime.now() - hard_time_window
    posts_with_attachments = PostsStorage.get_notification_posts(hard_time_offset)
    if len(posts_with_attachments) == 0:
        logging.info("Notification is not needed: no new posts")
        return
    posts, attachments = filter_original_posts(posts_with_attachments)
    logging.info("Start notification session")
    res = defaultdict(set)
    for post in posts:
        res[post.channel].add(post.post_id)
        if post in attachments:
            for post_id in attachments[post]:
                res[post.channel].add(post_id)

    loaded = {}
    for channel, post_ids in res.items():
        try:
            post_ids = list(post_ids)
            messages = await get_messages(channel, post_ids)
            for post_id, message in zip(post_ids, messages):
                loaded[(channel, post_id)] = message
        except Exception as e:
            logging.exception(e)
    sent_posts = []
    file_cache = {}
    disabled_users = set()
    for post in posts:
        user_id = post.user_id
        if user_id in disabled_users:
            continue
        await sleep(notification_single_timeout_s)
        posts_group = [post.post_id] + attachments[post]
        posts_group.sort()
        messages = [loaded[(post.channel, post_id)] for post_id in posts_group]
        logging.debug(f"Send message to {user_id}: {post.channel} {post.post_id}")
        try:
            await send_message(bot, user_id, messages, file_cache)
            sent_posts.append(post)
        except TelegramForbiddenError:
            logging.info(f"User {user_id} blocked the bot. Disable for this notification.")
            disabled_users.add(user_id)
        except Exception as e:
            logging.exception(e)
    update_seen_posts(sent_posts)
    for file in file_cache.values():
        os.remove(file)
    clear_cache_dir()
    logging.info("Complete notification session")


def clear_cache_dir():
    shutil.rmtree("bot/downloads", ignore_errors=True)


async def send_message(bot, user_id, messages: List, file_cache):
    main_message = messages[0]
    try:
        if len(messages) == 1 and main_message.text is not None:
            text, entities = create_text(main_message, main_message.text)
            await bot.send_message(user_id, text=text, entities=entities,
                                   disable_web_page_preview=True)
            return
        if main_message.media is not None:
            text = main_message.caption if main_message.caption is not None else ""
            if len(text) > MAX_CAPTION_LENGTH:
                text = text[:MAX_CAPTION_LENGTH] + "..."
            text, entities = create_text(main_message, text)
            media_group = MediaGroupBuilder(caption=text, caption_entities=entities)
            for message in messages:
                height, width = None, None
                if message.photo is not None:
                    file_id = message.photo.file_id
                elif message.video is not None:
                    file_id = message.video.file_id
                    height = message.video.height
                    width = message.video.width
                elif message.audio is not None:
                    file_id = message.audio.file_id
                elif message.document is not None:
                    file_id = message.document.file_id
                else:
                    logging.warning(f"Unknown file type {message.media}")
                    continue

                if file_id in file_cache:
                    file = file_cache[file_id]
                else:
                    file = await load_file(file_id)
                    file_cache[file_id] = file
                media_group.add(type=message.media.value, media=FSInputFile(file), height=height, width=width)
            media = media_group.build()
            if len(media) > 0:
                await bot.send_media_group(user_id, media=media)
                return
            else:
                logging.warning(f"No media found for message {main_message.id} in {main_message.chat.username}")
    except TelegramForbiddenError as e:
        raise e
    except Exception as e:
        logging.exception(e)
    message = messages[0]
    reaction = get_first_reaction(message)
    reaction = f"{reaction} " if reaction else ""
    await bot.send_message(user_id, parse_mode="markdown", text=f"{reaction}[{message.chat.title}]({message.link})")


def utf16len(s):
    # Encode the string into UTF-16 (result includes BOM)
    # Each UTF-16 symbol is represented by 2 bytes
    # We subtract 2 to get rid of Byte Order Mark
    return len(s.encode('utf-16')) // 2 - 1


def create_text(message: types.Message, text: str):
    entities = message.entities if message.entities is not None else []

    # repack entities from pyrogram to aiogram
    entities = [MessageEntity(type=e.type.name.lower(), offset=e.offset, length=e.length, url=e.url, user=e.user,
                              language=e.language, custom_emoji_id=str(e.custom_emoji_id)) for e in entities]

    # cut entities in case text is cut
    entities = [e for e in entities if e.offset < len(text)]
    for e in entities:
        if e.offset + e.length > len(text):
            e.length = len(text) - e.offset

    reaction = get_first_reaction(message)
    reaction = f"{reaction} " if reaction else ""

    # add chat name in the beginning
    if message.chat.type == ChatType.CHANNEL:
        chat_name = f"{reaction} {message.chat.title}:\n"
    else:
        author = f"{message.from_user.first_name} {message.from_user.last_name}"
        chat_name = f"{reaction} {message.chat.title} ({author}):\n"

    text = chat_name + text
    utf_16_chat_name_length = utf16len(chat_name)
    for e in entities:
        e.offset += utf_16_chat_name_length
    entities = [MessageEntity(type=MessageEntityType.BOLD, offset=0, length=utf_16_chat_name_length)] + entities

    # add link in the end
    link = f"\n{message.chat.username}"
    utf16_text_length = utf16len(text)
    utf_16_link_length = utf16len(link)
    entities.append(MessageEntity(type=MessageEntityType.TEXT_LINK, offset=utf16_text_length,
                                  length=utf_16_link_length, url=message.link))
    text += link
    return text, entities


def get_first_reaction(message) -> Optional[str]:
    try:
        if message.reactions is not None and len(message.reactions.reactions) > 0:
            return message.reactions.reactions[0].emoji
    except Exception as e:
        logging.exception(e)
    return None


async def scheduled_notification(bot):
    await sleep(initial_timeout_s)
    while True:
        if Context().stop:
            return
        try:
            await notify(bot)
        except Exception as e:
            logging.exception(e)
        if Context().stop:
            return
        await wait_unless_triggered(notification_timeout_s, Context().notification_event)


def init_notification(bot):
    loop = asyncio.get_event_loop()
    loop.create_task(scheduled_notification(bot))
