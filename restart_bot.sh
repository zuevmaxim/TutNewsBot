#!/bin/bash

if [ -f "env/sync.env" ]; then
  source env/sync.env
fi
if [ -z "$KEY_PATH" ] || [ -z "$TARGET_USER" ] || [ -z "$TARGET_HOST" ] || [ -z "$TARGET_PATH" ]; then
  echo "Missing required variables. Please check and re-run the script"
  exit 1
fi

echo "Stopping bot"
ssh -i "$KEY_PATH" "$TARGET_USER@$TARGET_HOST" "docker stop tutnews-bot" || exit 2
echo "Bot stopped"

echo "Sync files with release bot"
./sync.sh || exit 3

./sync_log.sh true || exit 4

echo "Restart bot"
ssh -i "$KEY_PATH" "$TARGET_USER@$TARGET_HOST" "cd $TARGET_PATH && ./build.sh" || exit 5

echo "Done"

