from typing import Optional

from aiogram import types
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.utils.keyboard import InlineKeyboardBuilder, ReplyKeyboardBuilder

from bot.config import DEFAULT_PERCENTILE, INTERESTING_PERCENTILES
from bot.messages import create_message
from bot.scrolling import trigger_scrolling
from bot.scrolling_utils import GetChatStatus
from bot.utils import extract_chanel_name
from storage.subscriptions_storage import SubscriptionStorage, Subscription


class Add(StatesGroup):
    chanel_name = State()


class Change(StatesGroup):
    chanel_name = State()


async def handle_add_subscription(message: types.Message, state: FSMContext):
    await state.set_state(Add.chanel_name)
    lang = message.from_user.language_code
    await message.answer(create_message("write.channel.name", lang))


async def handle_subscription_name(message: types.Message, safe_get_channel, state: Optional[FSMContext]):
    lang = message.from_user.language_code
    text = message.text
    channel = extract_chanel_name(text)
    if len(channel) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    if channel.startswith("+"):
        await message.answer(create_message("invitation.link.error", lang))
        return

    status, chat = await safe_get_channel(channel)
    if status.value == GetChatStatus.USER_NOT_EXIST.value:
        await message.answer(create_message("channel.not.found", lang, channel))
        return
    elif status.value == GetChatStatus.PRIVATE_CHAT.value:
        await message.answer(create_message("private.chat.error", lang, channel))
        return
    else:
        channel = chat.username

    if state is not None:
        # delete to remove keyboard
        data = await state.get_data()
        if "my_message" in data:
            await data["my_message"].delete()
        await state.clear()
    subscription = SubscriptionStorage.get_subscription(str(message.from_user.id), channel)
    if subscription is not None:
        await reply_subscription(message, channel, subscription.percentile, "existing.subscription")
    else:
        await reply_subscription(message, channel, DEFAULT_PERCENTILE)


async def reply_subscription(message, channel: str, percentile: int, message_key="add.subscription"):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    SubscriptionStorage.add_subscription(Subscription(user_id, channel, percentile))

    percentiles = list(INTERESTING_PERCENTILES)
    percentiles.remove(percentile)
    builder = InlineKeyboardBuilder()
    for p in percentiles:
        builder.button(text=create_message("change.subscription", lang, 100 - p),
                       callback_data=f"set_percentile;{channel};{p}")
    builder.adjust(1)
    text = create_message(message_key, lang, 100 - percentile, f"@{channel}")
    await message.bot.send_message(chat_id=user_id, text=text, reply_markup=builder.as_markup())
    trigger_scrolling()


async def process_callback_set_percentile(callback_query: types.CallbackQuery):
    channel, percentile = callback_query.data.split(";")[1:]
    percentile = int(percentile)
    await callback_query.message.delete()
    await reply_subscription(callback_query, channel, percentile)


async def handle_change_subscription(message: types.Message, state: FSMContext):
    await state.set_state(Change.chanel_name)
    await reply_choose_channel(message, state)


async def reply_choose_channel(message: types.Message, state: FSMContext = None):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    channels = SubscriptionStorage.get_subscription_names(user_id)
    builder = ReplyKeyboardBuilder()
    channels.sort()
    for channel in channels:
        builder.button(text=f"@{channel}")
    builder.adjust(2)
    answer = await message.answer(create_message("choose.channel", lang), reply_markup=builder.as_markup())
    # save to remove keyboard later
    if state is not None:
        await state.update_data(my_message=answer)
