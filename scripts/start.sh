#!/bin/bash
set -e

echo "Running database migrations..."

# Debug: show DATABASE_URL (without password)
echo "DATABASE_URL: ${DATABASE_URL:-EMPTY}@***"

# Run migrations
uv run alembic upgrade head

echo "Starting bot..."
exec uv run python -m src.main
