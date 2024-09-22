import logging

from bot.config import logging_user


async def log_to_user(bot, message: str):
    if logging_user is None:
        return
    try:
        await bot.send_message(logging_user, message)
    except Exception as e:
        logging.error("Error during sending message to user", e)
