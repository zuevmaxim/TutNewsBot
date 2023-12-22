LOCAL_PATH=$(pwd)
if [ -f "env/sync.env" ]; then
  source env/sync.env
fi

if [ -z "$KEY_PATH" ] || [ -z "$TARGET_USER" ] || [ -z "$TARGET_HOST" ] || [ -z "$TARGET_PATH" ]; then
  echo "Missing required variables. Please check and re-run the script"
  exit 1
fi

rsync -avhP \
  -e "ssh -i $KEY_PATH" \
  "$TARGET_USER@$TARGET_HOST:$TARGET_PATH/bot.log" "$LOCAL_PATH/"
