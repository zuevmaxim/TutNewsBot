# TutNews bot

This bot aggregates the most popular posts from a selected list of channels

## How to build and run

1. Install requirements
    ```
    pip3 install -r requirements.txt
    ```
2. Configure `BOT_TOKEN`, `API_ID`, and `API_HASH` environment variables.
   ```
   export $(grep -v '^#' env/release.env | xargs -d '\n')
   ```
3. Create and start container with databases
    ```
    docker-compose -f docker-compose.yaml up -d
    ```
4. Run `python3 bot/main.py`.
5. The scrolling application will ask for additional authentication via phone number, please contact project owners for
   details.


