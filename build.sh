#!/bin/sh
set -e

echo "Building dev image..."
docker compose build

echo "Starting database..."
docker compose up -d db

echo "Waiting for database to be ready..."
until docker compose exec db pg_isready -U ${DB_USER} -d ${DB_PASSWORD}; do
  echo "Waiting for db..."
  sleep 2
done

echo "Running migrations..."
# Necessary to do --entrypoint "" (setting to none). Otherwise, it would use the defined entrypoint script of the project.
docker compose run --rm --no-deps --entrypoint "" api alembic upgrade head

echo "Stopping containers..."
docker compose down

echo "Done. Run ./start.sh to start developing."