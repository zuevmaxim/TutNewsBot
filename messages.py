english_messages = {
    "start.info": "Hi! I can filter interesting news from your channels. Please use '/add [channel]' commang to add "
                  "subscription to a channel",
    "add.subscription": "I will notify you about interesting posts from {}",
    "empty.channel.name": "Please specify channel name",
    "channel.not.found": "Cannot find '{}' channel. Please check name",
    "remove.subscription": "I won't notify you about posts from {} channel",
    "remove.subscription.unknown": "Cannot unsubscribe from '{}' as you haven't been subscribed for this channel",
    "no.news": "There is no interesting news",
    "command.start": "Start bot",
    "command.add": "Add subscription for a channel",
    "command.remove": "Remove subscription",
}

russian_messages = {
    "start.info": "Привет! Я умею фильтровать интересные сообщения из твоих каналов. Используй команду "
                  "'/add [channel]', чтобы добавить подписку на канал",
    "add.subscription": "Буду уведомлять тебя об интересных сообщениях в {}",
    "empty.channel.name": "Укажи название канала",
    "channel.not.found": "Не могу найти '{}' канал. Укажи другое название",
    "remove.subscription": "Я отменил подписку на {}",
    "remove.subscription.unknown": "Не могу отменить подписку на '{}'. Ты не подписан на этот канал",
    "no.news": "Интересных новостей больше нет",
    "command.start": "Запустить бот",
    "command.add": "Добавить подписку на канал",
    "command.remove": "Отменить подписку",
}

lang_dictionary = {
    "en": english_messages,
    "ru": russian_messages,
}


def create_message(key, lang, *args):
    message = lang_dictionary[lang][key]
    if len(args) > 0:
        message = message.format(*args)
    return message


def check_dictionaries():
    assert english_messages.keys() == russian_messages.keys()


check_dictionaries()
