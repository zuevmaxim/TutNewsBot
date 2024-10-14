import asyncio
import logging
from typing import Optional

from bot.log import log_to_user


def extract_chanel_name(name: str) -> Optional[str]:
    if name is None:
        return None
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    if name.startswith("@"):
        name = name[1:]
    return name


def utf16len(s):
    # Encode the string into UTF-16 (result includes BOM)
    # Each UTF-16 symbol is represented by 2 bytes
    # We subtract 2 to get rid of Byte Order Mark
    return len(s.encode('utf-16')) // 2 - 1


async def wait_unless_triggered(timeout: int, event: asyncio.Event) -> bool:
    try:
        await asyncio.wait_for(event.wait(), timeout=timeout)
        event.clear()
        return True
    except asyncio.TimeoutError:
        return False


def create_message_link(channel, message):
    return message.link if message.chat is not None else f"https://t.me/{channel}/{message.id}"


async def should_skip_message(message, bot, channel: str):
    text = message.text if message.text is not None else message.caption
    if text is None or len(text.strip()) == 0:
        return False

    from ai.ai import should_skip_text
    skip = should_skip_text(text)
    if skip:
        link = create_message_link(channel, message)
        logging.warn(f"Message skipped: {link}\n{text}")
        await log_to_user(bot, f"Message skipped: {link}")
    return skip
