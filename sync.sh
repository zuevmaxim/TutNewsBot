#!/bin/bash

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
  --exclude '*.session*' \
  --include 'bot' \
  --include 'commands' \
  --include 'storage' \
  --include '.env' \
  --exclude '*.env' \
  --exclude 'sync.sh' \
  --exclude 'sync_log.sh' \
  --exclude '*.log' \
  --exclude '.git' \
  --exclude 'storage/dumps' \
  --exclude '.DS_Store' \
  --exclude '*__pycache__/' \
  --exclude '.idea' \
  --exclude 'local_build.sh' \
  --exclude '.gitignore' \
  --exclude '.run/' \
  "$LOCAL_PATH/" "$TARGET_USER@$TARGET_HOST:$TARGET_PATH"
