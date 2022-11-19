from aiogram import types
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State

from bot.messages import create_message
from bot.utils import extract_chanel_name
from commands.add import reply_choose_channel
from data.subscriptions import *


class Remove(StatesGroup):
    chanel_name = State()


async def handle_remove_subscription(message: types.Message):
    await Remove.chanel_name.set()
    await reply_choose_channel(message)


async def handle_subscription_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    subscription = extract_chanel_name(message.text)
    if len(subscription) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return
    await state.finish()
    result = remove_subscription(user_id, subscription)
    if result:
        await message.answer(create_message("remove.subscription", lang, f"@{subscription}"),
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer(create_message("remove.subscription.unknown", lang, subscription),
                             reply_markup=types.ReplyKeyboardRemove())
