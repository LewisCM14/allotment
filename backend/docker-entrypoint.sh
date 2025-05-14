#!/bin/bash
set -e

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application..."
# Use PORT env var, defaulting to 8000 if not set
exec uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}