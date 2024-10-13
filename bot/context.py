import logging


# This is a singleton context
class Context(object):
    _shared_state = {}

    def __new__(cls, *args, **kwargs):
        obj = super(Context, cls).__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_state
        return obj


def log_message_without_duplicates(level, message):
    context = Context()
    if message in context.cached_notifications:
        return
    context.cached_notifications.append(message)
    logging.log(level, message)
