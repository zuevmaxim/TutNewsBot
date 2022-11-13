import logging

from aiogram import Bot, Dispatcher, types, executor
from pyrogram.errors import BadRequest

from bot.config import bot_token
from bot.utils import pretty_int
from data.statistics import get_statistics
from data.subscriptions import *
from data.users import *
from messages import create_message
from notify import notify_user, init_notification
from scrolling import init_scrolling, get_channel

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


async def init_bot(dp, lang="en"):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("start", create_message("command.start", lang)),
            types.BotCommand("add", create_message("command.add", lang)),
            types.BotCommand("remove", create_message("command.remove", lang)),
        ]
    )


def extract_chanel_name(name):
    name = name.strip()
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    return name


@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    name = message.from_user.full_name
    add_user(User(user_id, name, lang))
    await init_bot(dp, lang)
    await message.answer(create_message("start.info", lang))


@dp.message_handler(commands=["add"])
async def handle_add_subscription(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    text = message.text
    subscription = extract_chanel_name(text[text.index("/add") + 4:])
    if len(subscription) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    try:
        await get_channel(subscription)
    except BadRequest as e:
        if e.ID == "USERNAME_INVALID":
            await message.answer(create_message("channel.not.found", lang, subscription))
            return
        logging.exception(e)

    add_subscription(Subscription(user_id, subscription))
    await message.answer(create_message("add.subscription", lang, subscription))


@dp.message_handler(commands=["remove"])
async def handle_remove_subscription(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    text = message.text
    subscription = extract_chanel_name(text[text.index("/remove") + 7:])
    if len(subscription) == 0:
        await message.answer(create_message("empty.channel.name", lang))
        return

    result = remove_subscription(user_id, subscription)
    if result:
        await message.answer(create_message("remove.subscription", lang, subscription))
    else:
        await message.answer(create_message("remove.subscription.unknown", lang, subscription))


@dp.message_handler(commands=["news"])
async def handle_news(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    count = await notify_user(bot, user_id)
    if count == 0:
        await message.answer(create_message("no.news", lang))


@dp.message_handler(commands=["list"])
async def handle_list(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    subscriptions = get_subscription_names(user_id)
    if len(subscriptions) == 0:
        await message.answer(create_message("list.subscriptions.empty", lang))
        return
    text = create_message("list.subscriptions", lang) + "\n"
    for channel in subscriptions:
        stat = get_statistics(channel)
        if stat is None:
            text += create_message("list.subscriptions.element", lang, channel)
        else:
            text += create_message("list.subscriptions.element.with.stat", lang, channel,
                                   pretty_int(stat.comments),
                                   pretty_int(stat.reactions))
        text += "\n"
    await message.answer(text)


if __name__ == "__main__":
    init_scrolling()
    init_notification(bot)
    executor.start_polling(dp, on_startup=init_bot, skip_updates=True)
