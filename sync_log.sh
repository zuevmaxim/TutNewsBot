LOCAL_PATH=$(pwd)
if [ -f "env/sync.env" ]; then
  source env/sync.env
fi

if [ -z "$KEY_PATH" ] || [ -z "$TARGET_USER" ] || [ -z "$TARGET_HOST" ] || [ -z "$TARGET_PATH" ]; then
  echo "Missing required variables. Please check and re-run the script"
  exit 1
fi

CLEAR_LOGS=$1

echo "Load log"
mkdir "$LOCAL_PATH/logs"
rsync -avhP \
  -e "ssh -i $KEY_PATH" \
  "$TARGET_USER@$TARGET_HOST:$TARGET_PATH/bot.log" "$LOCAL_PATH/logs/$(date +%Y%m%d-%H%M%S)-bot.log" || exit 2

if [ "$CLEAR_LOGS" = "true" ]; then
  echo "Clearing old logs"
  ssh -i "$KEY_PATH" "$TARGET_USER@$TARGET_HOST" "echo Start > $TARGET_PATH/bot.log" || exit 4
fi

echo "Done"
