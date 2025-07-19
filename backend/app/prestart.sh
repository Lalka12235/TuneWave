#!/usr/bin/env bash

set -e

echo "Run migrations"
alembic upgrade head
echo "Migrations apply"


exec "$@"