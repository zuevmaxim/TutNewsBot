from aiogram import types, Dispatcher
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import StatesGroup, State
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, KeyboardButton, ReplyKeyboardMarkup
from pyrogram.enums import ChatType
from pyrogram.errors import BadRequest

from bot.config import DEFAULT_PERCENTILE, INTERESTING_PERCENTILES
from bot.messages import create_message
from bot.utils import extract_chanel_name
from storage.subscriptions_storage import SubscriptionStorage, Subscription


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

    try:
        chat = await get_channel(channel)
        public_chat = chat.type == ChatType.CHANNEL or\
                      (chat.type == ChatType.GROUP or chat.type == ChatType.SUPERGROUP) and chat.username is not None
        if not public_chat or chat.type == ChatType.PRIVATE or chat.type == ChatType.BOT:
            await message.answer(create_message("private.chat.error", lang, channel))
            return
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID" or e.ID == "USERNAME_NOT_OCCUPIED":
            await message.answer(create_message("channel.not.found", lang, channel))
            return
        raise e

    # delete to remove keyboard
    async with state.proxy() as data:
        if "my_message" in data:
            my_message = data["my_message"]
            await my_message.delete()

    await state.finish()
    subscription = SubscriptionStorage.get_subscription(message.from_user.id, channel)
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
    markup = InlineKeyboardMarkup()
    for p in percentiles:
        button = InlineKeyboardButton(create_message("change.subscription", lang, 100 - p),
                                      callback_data=f"set_percentile;{channel};{p}")
        markup.add(button)
    text = create_message(message_key, lang, 100 - percentile, f"@{channel}")
    await message.bot.send_message(user_id, text, reply_markup=markup)


async def process_callback_set_percentile(callback_query: types.CallbackQuery):
    channel, percentile = callback_query.data.split(";")[1:]
    percentile = int(percentile)
    await callback_query.answer()
    await callback_query.message.delete()
    await reply_subscription(callback_query, channel, percentile)


async def handle_change_subscription(message: types.Message):
    await Change.chanel_name.set()
    await reply_choose_channel(message, Dispatcher.get_current().current_state())


async def reply_choose_channel(message: types.Message, state: FSMContext = None):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    channels = SubscriptionStorage.get_subscription_names(user_id)
    markup = ReplyKeyboardMarkup(resize_keyboard=True, one_time_keyboard=True, row_width=2)
    channels.sort()
    for channel in channels:
        markup.insert(KeyboardButton(f"@{channel}"))
    answer = await message.answer(create_message("choose.channel", lang), reply_markup=markup)
    # save to remove keyboard later
    if state is not None:
        async with state.proxy() as data:
            data["my_message"] = answer
