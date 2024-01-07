import asyncio
import logging

from aiogram import Bot, Dispatcher, types
from aiogram.filters import CommandStart, Command, StateFilter
from aiogram.fsm.context import FSMContext
from aiogram.fsm.storage.memory import MemoryStorage

import commands.add
import commands.remove
import commands.start
from bot.config import *
from bot.context import Context
from bot.scrolling_utils import safe_get_channel
from messages import create_message
from notify import init_notification
from scrolling import init_scrolling
from storage.postgres import db


def setup_logging():
    logging.getLogger().setLevel(logging.INFO)
    formatter = logging.Formatter("%(asctime)s [%(levelname)-7.7s]  %(message)s")

    file_handler = logging.FileHandler("bot.log", mode="a")
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.WARNING)
    logging.getLogger().addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    console_handler.setLevel(logging.INFO)
    logging.getLogger().addHandler(console_handler)


dp = Dispatcher(storage=MemoryStorage())


async def init_bot(bot, lang="en"):
    await bot.set_my_commands(
        [
            types.BotCommand(command="add", description=create_message("command.add", lang)),
            types.BotCommand(command="setup", description=create_message("command.change", lang)),
            types.BotCommand(command="remove", description=create_message("command.remove", lang)),
            types.BotCommand(command="cancel", description=create_message("command.cancel", lang)),
        ]
    )


def shutdown_bot():
    db.close()
    Context().stop = True


async def safe_call(f, message):
    try:
        await f()
    except Exception as e:
        logging.exception(e)
        lang = message.from_user.language_code
        await message.answer(create_message("internal.error", lang))


@dp.message(Command('cancel'))
async def cancel_handler(message: types.Message, state: FSMContext):
    lang = message.from_user.language_code
    current_state = await state.get_state()
    if current_state is not None:
        logging.info('Cancelling state %r', current_state)
        await state.clear()
    await message.answer(create_message("command.cancel.reaction", lang), reply_markup=types.ReplyKeyboardRemove())


@dp.message(CommandStart())
async def handle_start(message: types.Message):
    await safe_call(lambda: commands.start.handle_start(message), message)


@dp.message(Command('add'))
async def handle_add_subscription(message: types.Message, state: FSMContext):
    await safe_call(lambda: commands.add.handle_add_subscription(message, state), message)


@dp.message(StateFilter(commands.add.Add.chanel_name, commands.add.Change.chanel_name))
async def handle_subscription_name(message: types.Message, state: FSMContext):
    # This is a hack: cannot call get_channel from commands/add.py for some reason
    await safe_call(lambda: commands.add.handle_subscription_name(message, safe_get_channel, state), message)


@dp.message(Command('setup'))
async def handle_change_subscription(message: types.Message, state: FSMContext):
    await safe_call(lambda: commands.add.handle_change_subscription(message, state), message)


@dp.callback_query(lambda c: c.data.startswith("set_percentile;"))
async def process_callback_set_percentile(callback_query: types.CallbackQuery):
    await safe_call(lambda: commands.add.process_callback_set_percentile(callback_query), callback_query)


@dp.message(Command('remove'))
async def handle_remove_subscription(message: types.Message, state: FSMContext):
    await safe_call(lambda: commands.remove.handle_remove_subscription(message, state), message)


@dp.message(StateFilter(commands.remove.Remove.chanel_name))
async def handle_remove_subscription_name(message: types.Message, state: FSMContext):
    await safe_call(lambda: commands.remove.handle_subscription_name(message, state), message)


@dp.message()
async def text_add_handler(message: types.Message):
    await safe_call(lambda: commands.add.handle_subscription_name(message, safe_get_channel, None), message)


async def main(bot: Bot):
    await init_bot(bot)
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot, polling_timeout=30)


if __name__ == "__main__":
    try:
        setup_logging()
        context = Context()
        context.stop = False
        context.scrolling_event = asyncio.Event()
        context.notification_event = asyncio.Event()

        bot = Bot(token=bot_token)
        init_scrolling()
        init_notification(bot)
        loop = asyncio.get_event_loop()
        loop.run_until_complete(main(bot))
    finally:
        shutdown_bot()
