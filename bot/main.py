import logging

from aiogram import Bot, Dispatcher, types, executor
from pyrogram.errors import BadRequest

from bot.config import *
from bot.utils import pretty_int
from data.statistics import get_statistics
from data.subscriptions import *
from data.users import *
from messages import create_message
from notify import notify_user, init_notification
from scrolling import init_scrolling, get_channel

formatter = logging.Formatter("%(asctime)s [%(levelname)-7.7s]  %(message)s")
handlers = [
    logging.FileHandler("bot.log", mode="w"),
    logging.StreamHandler(),
]
logging.getLogger().setLevel(logging.INFO)
for handler in handlers:
    handler.setFormatter(formatter)
    handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(handler)

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
        logging.exception(e)

    add_subscription(Subscription(user_id, channel, percentile))
    percentile = PERCENTILE_HIGH if percentile == "high" else PERCENTILE_BASIC
    await message.answer(create_message("add.subscription", lang, 100 - percentile, channel))


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
    subscriptions = get_subscriptions(user_id)
    if len(subscriptions) == 0:
        await message.answer(create_message("list.subscriptions.empty", lang))
        return
    text = create_message("list.subscriptions", lang) + "\n"
    for subscription in subscriptions:
        stat = get_statistics(subscription.channel)
        if stat is None:
            text += create_message("list.subscriptions.element", lang, subscription.channel)
        else:
            comments, reactions = stat.get_percentiles(subscription.percentile)
            text += create_message("list.subscriptions.element.with.stat", lang, subscription.channel,
                                   pretty_int(comments),
                                   pretty_int(reactions))
        text += "\n"
    await message.answer(text)


if __name__ == "__main__":
    init_scrolling()
    init_notification(bot)
    executor.start_polling(dp, on_startup=init_bot, skip_updates=True)
