from aiogram import types

from bot.messages import create_message
from storage.user_storage import UserStorage, User


async def handle_start(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    UserStorage.add_user(User(user_id, lang))
    await message.answer(create_message("start.info", lang))
