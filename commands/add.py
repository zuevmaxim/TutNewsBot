import logging

from aiogram import types
from pyrogram.errors import BadRequest

from bot.config import PERCENTILE_HIGH, PERCENTILE_BASIC
from bot.messages import create_message
from bot.utils import extract_chanel_name
from data.subscriptions import *


async def handle_add_subscription(message: types.Message, get_channel):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    text = message.text
    text = text[text.index("/add") + 4:]
    parts = [element for element in text.split(" ") if len(element) > 0]
    if len(parts) > 2:
        await message.answer(create_message("add.incorrect.params", lang))
        return
    if len(parts) < 1:
        await message.answer(create_message("empty.channel.name", lang))
        return
    percentile = "basic" if len(parts) == 1 else parts[1]
    if percentile != "basic" and percentile != "high":
        await message.answer(create_message("add.incorrect.percentile", lang))
        return
    channel = extract_chanel_name(parts[0])
    if len(channel) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    try:
        await get_channel(channel)
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID" or e.ID == "USERNAME_NOT_OCCUPIED":
            await message.answer(create_message("channel.not.found", lang, channel))
            return
        raise e

    add_subscription(Subscription(user_id, channel, percentile))
    percentile = PERCENTILE_HIGH if percentile == "high" else PERCENTILE_BASIC
    await message.answer(create_message("add.subscription", lang, 100 - percentile, channel))
