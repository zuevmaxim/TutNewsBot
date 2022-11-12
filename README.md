# TelegramAggregatorBot
This bot aggregates the most popular posts from a selected list of channels


## How to build and run

1. Install requirements
    ```
    pip3 install -r requirements.txt
    ```

2. Create databases
    ```
    ./bd/create_bd.sh
    ```
   
3. Run `main.py`. Make sure that you have configured `BOT_TOKEN`, `API_ID` and `API_HASH` in environment variables.
4. The scrolling application will ask for additional authentication via phone number, please contact project owners for details.


