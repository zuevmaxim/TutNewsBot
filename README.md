# TutNews bot

This bot aggregates the most popular posts from a selected list of channels

## How it works

1. Add interesting _public_ channels to the bot.
2. The bot will periodically scan these channels.
3. It will then send back only the most popular posts based on the number of comments and reactions on Telegram.
4. You can customize the percentage of top-rated posts you want to receive.

Join: [@tutnewsbot](https://t.me/tutnewsbot)

## How to build and run

1. Configure `BOT_TOKEN`, `API_ID`, and `API_HASH` environment variables in `env/release.env` file.
2. Create and start container with database and bot: `./build.sh`
3. The scrolling application will ask for additional authentication via phone number, please contact project owners for
   details.


