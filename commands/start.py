from aiogram import types

from bot.messages import create_message
from data.users import *


async def handle_start(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    name = message.from_user.full_name
    add_user(User(user_id, name, lang))
    await message.answer(create_message("start.info", lang))
