from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State

from bot.messages import create_message
from bot.utils import extract_chanel_name
from commands.add import reply_choose_channel
from storage.subscriptions_storage import SubscriptionStorage


class Remove(StatesGroup):
    chanel_name = State()


async def handle_remove_subscription(message: types.Message, state: FSMContext):
    await state.set_state(Remove.chanel_name)
    await reply_choose_channel(message)


async def handle_subscription_name(message: types.Message, state: FSMContext):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    text = message.text
    if text is None:
        await message.answer(create_message("empty.channel.name", lang))
        return
    channel = extract_chanel_name(text)
    if len(channel) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return
    await state.clear()
    subscription = SubscriptionStorage.get_subscription(str(user_id), channel)
    if subscription is not None:
        SubscriptionStorage.remove_subscription(str(user_id), channel)
        await message.answer(create_message("remove.subscription", lang, f"@{channel}"),
                             reply_markup=types.ReplyKeyboardRemove())
    else:
        await message.answer(create_message("remove.subscription.unknown", lang, channel),
                             reply_markup=types.ReplyKeyboardRemove())
