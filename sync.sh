#!/bin/bash

rsync -avhP \
  -e "ssh -i $KEY_PATH" \
  --exclude '*.session*' \
  --include 'bot' \
  --include 'commands' \
  --include 'storage' \
  --include '.env' \
  --exclude '*.env' \
  --exclude 'sync.sh' \
  --exclude '*.log' \
  --exclude 'storage/persist/*' \
  --exclude '.git' \
  --exclude '.DS_Store' \
  --exclude '*__pycache__/' \
  --exclude '.idea' \
  $LOCAL_PATH $TARGET_USER@$TARGET_HOST:$TARGET_PATH

# export $(grep -v '^#' env/sync.env | xargs)
