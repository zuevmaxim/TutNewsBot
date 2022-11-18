import logging

from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from bot.config import PERCENTILE_HIGH, PERCENTILE_BASIC
from bot.messages import create_message
from bot.utils import extract_chanel_name
from data.subscriptions import *


class Add(StatesGroup):
    chanel_name = State()


async def handle_add_subscription(message: types.Message):
    await Add.chanel_name.set()
    lang = message.from_user.language_code
    await message.answer(create_message("write.channel.name", lang))


async def handle_subscription_name(message: types.Message, get_channel, state: FSMContext):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    text = message.text
    channel = extract_chanel_name(text)
    if len(channel) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    try:
        chat = await get_channel(channel)
        if chat.type != ChatType.CHANNEL:
            await message.answer(create_message("bad.type.of.channel", lang, channel))
            return
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID" or e.ID == "USERNAME_NOT_OCCUPIED":
            await message.answer(create_message("channel.not.found", lang, channel))
            return
        raise e
    await state.finish()
    percentile = "basic"
    add_subscription(Subscription(user_id, channel, percentile))
    percentile = PERCENTILE_HIGH if percentile == "high" else PERCENTILE_BASIC
    await message.answer(create_message("add.subscription", lang, 100 - percentile, channel))


