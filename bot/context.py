# This is a singleton context
class Context(object):
    _shared_state = {}

    def __new__(cls, *args, **kwargs):
        obj = super(Context, cls).__new__(cls, *args, **kwargs)
        obj.__dict__ = cls._shared_state
        return obj
