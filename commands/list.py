from aiogram import types

from bot.messages import create_message
from bot.utils import pretty_int
from data.statistics import get_statistics
from data.subscriptions import get_subscriptions


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
