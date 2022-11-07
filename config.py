import os
import datetime

bot_token = os.environ["BOT_TOKEN"]
api_id = os.environ["API_ID"]
api_hash = os.environ["API_HASH"]

MINUTE = 60
scrolling_timeout_s = 1 * MINUTE
scrolling_single_timeout_s = 0.5

hard_time_window = datetime.timedelta(days=1)
soft_time_window = datetime.timedelta(hours=1)

notification_timeout_s = 5 * MINUTE
notification_single_timeout_s = 0.5
