#!/bin/bash
set -e

# Function to check if postgres is ready
postgres_ready() {
  python -c "
import sys
from sqlalchemy import create_engine
from urllib.parse import urlparse
import os

url = os.environ.get('DATABASE_URL', '')
if not url:
    sys.exit(1)

result = urlparse(url)
try:
    engine = create_engine(url)
    conn = engine.connect()
    conn.close()
    sys.exit(0)
except Exception:
    sys.exit(1)
"
}

echo "Waiting for PostgreSQL to become available..."
# Wait for PostgreSQL to become available
RETRIES=15
until postgres_ready || [ $RETRIES -eq 0 ]; do
  echo "Waiting for PostgreSQL server, $((RETRIES--)) remaining attempts..."
  sleep 2
done

if [ $RETRIES -eq 0 ]; then
  echo "Error: PostgreSQL not available after multiple attempts"
  exit 1
fi

echo "PostgreSQL is available"

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000