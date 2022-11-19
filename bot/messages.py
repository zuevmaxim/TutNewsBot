english_messages = {
    "start.info": "Hi! I can filter interesting news from your channels. Please use /add command to add "
                  "subscription to a channel",
    "add.subscription": "I will notify you about top {}% of posts from {}",
    "existing.subscription": "I notify you about top {}% of posts from {}",
    "change.subscription": "Notify about top {}%",
    "choose.channel": "Choose channel",
    "empty.channel.name": "Please specify channel name",
    "channel.not.found": "Cannot find '{}' channel. Please check name",
    "remove.subscription": "I won't notify you about posts from {} channel",
    "remove.subscription.unknown": "Cannot unsubscribe from '{}' as you haven't been subscribed for this channel",
    "no.news": "There is no interesting news",
    "command.start": "Start bot",
    "command.add": "Add subscription for a channel",
    "command.change": "Change notification level of a subscription",
    "write.channel.name": "Please write the name of the channel",
    "command.remove": "Remove subscription",
    "command.cancel": "Cancel the current operation",
    "command.cancel.reaction": "Command canceled",
    "bad.type.of.channel": "It is not a channel. Try something else",
    "list.subscriptions.empty": "You have no subscriptions",
    "list.subscriptions": "Your subscriptions:",
    "list.subscriptions.element.with.stat": "{} ({} comments, {} reactions)",
    "list.subscriptions.element": "{}",
    "internal.error": "Internal bot error",
}

russian_messages = {
    "start.info": "Привет! Я умею фильтровать интересные сообщения из твоих каналов. Используй команду "
                  "/add, чтобы добавить подписку на канал",
    "add.subscription": "Буду уведомлять тебя о топ {}% постов в {}",
    "existing.subscription": "Я уведомляю тебя о топ {}% постов в {}",
    "change.subscription": "Уведомляй о топ {}%",
    "choose.channel": "Выбери канал",
    "empty.channel.name": "Укажи название канала",
    "channel.not.found": "Не могу найти '{}' канал. Укажи другое название",
    "remove.subscription": "Я отменил подписку на {}",
    "remove.subscription.unknown": "Не могу отменить подписку на '{}'. Ты не подписан на этот канал",
    "no.news": "Интересных новостей больше нет",
    "command.start": "Запустить бот",
    "command.add": "Добавить подписку на канал",
    "command.change": "Изменить количество уведомлений для подписки",
    "write.channel.name": "Укажи название канала",
    "command.remove": "Отменить подписку",
    "command.cancel": "Отменить текущую операцию",
    "command.cancel.reaction": "Команда отменена",
    "bad.type.of.channel": "Это не канал, попробуй что-нибудь ещё",
    "list.subscriptions.empty": "У тебя нет ни одной подписки",
    "list.subscriptions": "Твои подписки:",
    "list.subscriptions.element.with.stat": "{} ({} комментариев, {} реакций)",
    "list.subscriptions.element": "{}",
    "internal.error": "У меня произошла ошибка",
}

lang_dictionary = {
    "en": english_messages,
    "ru": russian_messages,
}


def create_message(key, lang, *args):
    if lang not in lang_dictionary:
        lang = "en"
    message = lang_dictionary[lang][key]
    if len(args) > 0:
        message = message.format(*args)
    return message


def check_dictionaries():
    assert english_messages.keys() == russian_messages.keys()


check_dictionaries()
