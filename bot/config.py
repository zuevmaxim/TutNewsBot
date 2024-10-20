import datetime
import os

bot_token = os.environ["BOT_TOKEN"]
api_id = os.environ["API_ID"]
api_hash = os.environ["API_HASH"]


def get_env_or(key, default_value):
    if key in os.environ:
        return os.environ[key]
    return default_value


MINUTE = 60
initial_timeout_s = 5
scrolling_timeout_s = int(get_env_or("SCROLLING_TIMEOUT_MIN", 11)) * MINUTE
scrolling_single_timeout_s = 0.5
notification_single_timeout_s = 1
internal_error_timeout_s = 10

hard_time_window = datetime.timedelta(days=1)
soft_time_window = datetime.timedelta(hours=6)
news_drop_time = datetime.timedelta(weeks=1)

INTERESTING_PERCENTILES = [0, 25, 50, 75, 90, 95, 99]
DEFAULT_PERCENTILE = 95
logging_user = get_env_or("LOG_USER_ID", None)
