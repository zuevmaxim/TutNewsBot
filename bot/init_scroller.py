import os

from pyrogram import Client

api_id = os.environ["API_ID"]
api_hash = os.environ["API_HASH"]
app = Client("scroller", api_id=api_id, api_hash=api_hash)

if __name__ == "__main__":
    with app:
        print("OK")
