import logging

from aiogram import Bot, Dispatcher, types, executor
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text

import commands.add
import commands.list
import commands.news
import commands.remove
import commands.start
from bot.config import *
from commands import add
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
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


async def init_bot(dp, lang="en"):
    await dp.bot.set_my_commands(
        [
            types.BotCommand("add", create_message("command.add", lang)),
            types.BotCommand("setup", create_message("command.change", lang)),
            types.BotCommand("remove", create_message("command.remove", lang)),
            types.BotCommand("cancel", create_message("command.cancel", lang)),
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
        user_id = message.from_user.id
        lang = message.from_user.language_code
        await bot.send_message(user_id, create_message("internal.error", lang))


@dp.message_handler(state='*', commands=['cancel'])
@dp.message_handler(Text(equals='cancel', ignore_case=True), state='*')
async def cancel_handler(message: types.Message, state: FSMContext):
    lang = message.from_user.language_code
    current_state = await state.get_state()
    if current_state is None:
        return

    logging.info('Cancelling state %r', current_state)
    await state.finish()
    await message.answer(create_message("command.cancel.reaction", lang), reply_markup=types.ReplyKeyboardRemove())


@dp.message_handler(commands=["start"])
async def handle_start(message: types.Message):
    await safe_call(lambda: commands.start.handle_start(message), message)


@dp.message_handler(commands=["add"])
async def handle_add_subscription(message: types.Message):
    await safe_call(lambda: commands.add.handle_add_subscription(message), message)


@dp.message_handler(state=[commands.add.Add.chanel_name, commands.add.Change.chanel_name])
async def handle_subscription_name(message: types.Message, state: FSMContext):
    # This is a hack: cannot call get_channel from commands/add.py for some reason
    await safe_call(lambda: add.handle_subscription_name(message, lambda name: get_channel(name), state), message)

@dp.message_handler(commands=["setup"])
async def handle_change_subscription(message: types.Message):
    await safe_call(lambda: commands.add.handle_change_subscription(message), message)


@dp.callback_query_handler(lambda c: c.data.startswith("set_percentile;"))
async def process_callback_set_percentile(callback_query: types.CallbackQuery):
    await safe_call(lambda: add.process_callback_set_percentile(callback_query), callback_query)


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
