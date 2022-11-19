from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from bot.config import PERCENTILE_HIGH, PERCENTILE_BASIC
from bot.messages import create_message
from bot.utils import extract_chanel_name
from data.subscriptions import *


class Add(StatesGroup):
    chanel_name = State()


class Change(StatesGroup):
    chanel_name = State()


async def handle_add_subscription(message: types.Message):
    await Add.chanel_name.set()
    lang = message.from_user.language_code
    await message.answer(create_message("write.channel.name", lang))


async def handle_subscription_name(message: types.Message, get_channel, state: FSMContext):
    lang = message.from_user.language_code
    text = message.text
    channel = extract_chanel_name(text)
    if len(channel) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    if (await state.get_state()).startswith("Add"):
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
    subscription = get_subscription(message.from_user.id, channel)
    if subscription is not None:
        await reply_subscription(message, channel, subscription.percentile, "existing.subscription")
    else:
        await reply_subscription(message, channel, "basic")


async def reply_subscription(message, channel, percentile, message_key="add.subscription"):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    add_subscription(Subscription(user_id, channel, percentile))

    other_percentile = "basic" if percentile == "high" else "high"
    change_percentile_button = InlineKeyboardButton(
        create_message("change.subscription", lang, 100 - percentile_number(other_percentile)),
        callback_data=f"set_percentile;{channel};{other_percentile}")
    markup = InlineKeyboardMarkup().add(change_percentile_button)
    text = create_message(message_key, lang, 100 - percentile_number(percentile), f"@{channel}")
    await message.bot.send_message(user_id, text, reply_markup=markup)


async def process_callback_set_percentile(callback_query: types.CallbackQuery):
    channel, percentile = callback_query.data.split(";")[1:]
    await callback_query.answer()
    await callback_query.message.delete()
    await reply_subscription(callback_query, channel, percentile)


def percentile_number(percentile):
    return PERCENTILE_HIGH if percentile == "high" else PERCENTILE_BASIC


async def handle_change_subscription(message: types.Message):
    await Change.chanel_name.set()
    await reply_choose_channel(message)


async def reply_choose_channel(message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    channels = get_subscription_names(user_id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    for channel in channels:
        markup.insert(KeyboardButton(f"@{channel}"))
    await message.answer(create_message("choose.channel", lang), reply_markup=markup)
