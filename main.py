from aiogram import Bot, Dispatcher, types, executor
from data.users import *
from data.subscriptions import *
from notify import notify_user, init_notification
from scrolling import init_scrolling
from config import bot_token
import logging

logging.basicConfig(level=logging.INFO)

bot = Bot(token=bot_token)
dp = Dispatcher(bot)


def extract_chanel_name(name):
    prefix = "https://t.me/"
    if name[:len(prefix)] == prefix:
        name = name[len(prefix):]
    return name


@dp.message_handler(commands=['start'])
async def handle_start(message: types.Message):
    user_id = message.from_user.id
    name = message.from_user.full_name
    add_user(User(user_id, name))
    await message.answer("Welcome")


@dp.message_handler(commands=['add'])
async def handle_add_subscription(message: types.Message):
    user_id = message.from_user.id
    subscription = extract_chanel_name(message.text[5:])
    add_subscription(Subscription(user_id, subscription))
    await message.answer(f"We will add {subscription} to the list of your subscriptions")


@dp.message_handler(commands=['remove'])
async def handle_remove_subscription(message: types.Message):
    user_id = message.from_user.id
    subscription = extract_chanel_name(message.text[8:])

    result = remove_subscription(user_id, subscription)
    if result:
        await message.answer(f"We will remove {subscription} from the list of your subscriptions")
    else:
        await message.answer(f"{subscription} is not in the list of your subscriptions")


@dp.message_handler(commands=['news'])
async def handle_news(message: types.Message):
    user_id = message.from_user.id
    count = await notify_user(bot, user_id)
    if count == 0:
        await message.answer("No more news")


if __name__ == '__main__':
    init_scrolling()
    init_notification(bot)
    executor.start_polling(dp, skip_updates=True)
