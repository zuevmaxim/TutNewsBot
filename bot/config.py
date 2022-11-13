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
scrolling_timeout_s = int(get_env_or("SCROLLING_TIMEOUT_MIN", 10)) * MINUTE
scrolling_single_timeout_s = 0.5

hard_time_window = datetime.timedelta(days=1)
soft_time_window = datetime.timedelta(hours=3)
news_drop_time = datetime.timedelta(weeks=1)

notification_timeout_s = int(get_env_or("NOTIFICATION_TIMEOUT_MIN", 15)) * MINUTE
notification_single_timeout_s = 0.5

statistics_update_s = 10 * MINUTE
comments_percentile = 95
reactions_percentile = 95
