import logging

from aiogram import Bot, Dispatcher, types, executor

import commands.add
import commands.list
import commands.news
import commands.remove
import commands.start
from bot.config import *
from data.utils import close_db
from messages import create_message
from notify import init_notification, stop_notifications
from scrolling import init_scrolling, get_channel, stop_scrolling

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


async def shutdown_bot(dp):
    close_db()
    stop_scrolling()
    stop_notifications()


async def safe_call(f, message):
    try:
        await f()
    except Exception as e:
        logging.exception(e)
        lang = message.from_user.language_code
        await message.answer(create_message("internal.error", lang))


@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await safe_call(lambda: commands.start.handle_start(message), message)


@dp.message_handler(commands=["add"])
async def handle_add_subscription(message: types.Message):
    # This is a hack: cannot call get_channel from commands/add.py for some reason
    await safe_call(lambda: commands.add.handle_add_subscription(message, lambda name: get_channel(name)), message)


@dp.message_handler(commands=["remove"])
async def handle_remove_subscription(message: types.Message):
    await safe_call(lambda: commands.remove.handle_remove_subscription(message), message)


@dp.message_handler(commands=["news"])
async def handle_news(message: types.Message):
    await safe_call(lambda: commands.news.handle_news(message), message)


@dp.message_handler(commands=["list"])
async def handle_list(message: types.Message):
    await safe_call(lambda: commands.list.handle_list(message), message)


if __name__ == "__main__":
    init_scrolling()
    init_notification(bot)
    executor.start_polling(dp, on_startup=init_bot, on_shutdown=shutdown_bot, skip_updates=True)
