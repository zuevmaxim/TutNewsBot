from aiogram import types

from bot.messages import create_message
from bot.notify import notify_user


async def handle_news(message: types.Message):
    user_id = message.from_user.id
    lang = message.from_user.language_code
    count = await notify_user(message.bot, user_id)
    if count == 0:
        await message.answer(create_message("no.news", lang))
