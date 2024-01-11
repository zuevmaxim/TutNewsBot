#! /bin/bash

if [ -f "env/release.env" ]; then
  set -a
  source env/release.env
  set +a
fi

if [ -z "$POSTGRES_DB" ] || [ -z "$POSTGRES_USER" ] || [ -z "$POSTGRES_PASSWORD" ] ||
   [ -z "$POSTGRES_PORT" ]; then
  echo "Missing required variables. Please check and re-run the script"
  exit 1
fi

docker-compose -f docker-compose.yaml up -d

