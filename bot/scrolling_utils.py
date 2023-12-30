from enum import Enum
from typing import List

from pyrogram import Client, types
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from bot.config import api_id, api_hash

app = Client("scroller", api_id=api_id, api_hash=api_hash)


class GetChatStatus(Enum):
    SUCCESS = "success"
    USER_NOT_EXIST = "user does not exist"
    PRIVATE_CHAT = "chat is private"


async def safe_get_channel(channel: str):
    try:
        chat = await app.get_chat(chat_id=f"@{channel}")
        # ChatType.PRIVATE and ChatType.BOT are restricted
        is_chat_or_channel = chat.type == ChatType.CHANNEL or \
                             chat.type == ChatType.GROUP or \
                             chat.type == ChatType.SUPERGROUP
        if is_chat_or_channel:
            if chat.username is None:
                # some channel may have no ID set for samo reason
                chat.username = channel
            return GetChatStatus.SUCCESS, chat
        return GetChatStatus.PRIVATE_CHAT, chat
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID" or e.ID == "USERNAME_NOT_OCCUPIED":
            return GetChatStatus.USER_NOT_EXIST, None
        raise e


async def get_messages(channel: str, post_ids: List[int]) -> List[types.Message]:
    return await app.get_messages(chat_id=f"@{channel}", message_ids=post_ids)


async def load_file(file_id: str) -> str:
    return await app.download_media(file_id)
