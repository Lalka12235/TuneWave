#!/usr/bin/env bash
set -e
.venv/bin/alembic upgrade head

exec "$@"