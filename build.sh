#! /bin/bash

if [ -f "env/local.env" ]; then
  set -a
  source env/local.env
  set +a
fi

if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] ||
   [ -z "$POSTGRES_HOST" ] || [ -z "$POSTGRES_PORT" ]; then
  echo "Missing required variables. Please check and re-run the script"
  exit 1
fi

docker-compose -f docker-compose.yaml up -d

