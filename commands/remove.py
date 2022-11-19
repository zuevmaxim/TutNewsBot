from aiogram import types

from bot.messages import create_message
from bot.utils import extract_chanel_name
from data.subscriptions import *


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
        await message.answer(create_message("remove.subscription", lang, f"@{subscription}"))
    else:
        await message.answer(create_message("remove.subscription.unknown", lang, subscription))
