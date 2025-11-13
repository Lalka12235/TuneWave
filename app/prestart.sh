#!/usr/bin/env bash

set -e

echo "Environment variables for DB:"
printenv | grep -E "DB_USER|DB_PASS|DB_NAME|APP_CONFIG_DB_URL" || true

echo "Waiting for PostgreSQL to be ready..."
until PGPASSWORD=$DB_PASS psql -h postgres -U $DB_USER -c '\q'; do
  >&2 echo "Postgres is unavailable - sleeping"
  sleep 1
done

>&2 echo "Postgres is up - executing command"

echo "Run migrations"
# 🔥 Изменено: Используем полный путь к исполняемому файлу alembic
/app/.venv/bin/alembic upgrade head
echo "Migrations applied"


exec "$@"