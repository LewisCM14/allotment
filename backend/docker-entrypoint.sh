#!/bin/bash
set -e

# Function to check if postgres is ready
postgres_ready() {
  python -c "
import sys
from sqlalchemy import create_engine
from urllib.parse import urlparse
import os
import time

url = os.environ.get('DATABASE_URL', '')
if not url:
    print('ERROR: DATABASE_URL environment variable is not set')
    sys.exit(1)

# Print database connection info (hide password)
result = urlparse(url)
safe_url = f'{result.scheme}://{result.username}:******@{result.hostname}:{result.port}{result.path}'
print(f'Attempting to connect to: {safe_url}')

try:
    engine = create_engine(url)
    conn = engine.connect()
    conn.close()
    print('Connection successful!')
    sys.exit(0)
except Exception as e:
    print(f'Connection failed: {str(e)}')
    sys.exit(1)
"
}

echo "Waiting for PostgreSQL to become available..."
# Wait for PostgreSQL to become available
RETRIES=30
until postgres_ready || [ $RETRIES -eq 0 ]; do
  echo "Waiting for PostgreSQL server, $((RETRIES--)) remaining attempts..."
  sleep 5
done

if [ $RETRIES -eq 0 ]; then
  echo "Error: PostgreSQL not available after multiple attempts"
  echo "Please check your DATABASE_URL environment variable and ensure the PostgreSQL server is running"
  
  echo "Environment details:"
  echo "DATABASE_URL: $(echo $DATABASE_URL | sed 's/[:@].*[:@]/:*****@/')"
  echo "HOSTNAME: $(hostname)"
  echo "Network information:"
  ip addr show
  
  exit 1
fi

echo "PostgreSQL is available"

echo "Running database migrations..."
python -m alembic upgrade head

echo "Starting application..."
exec uvicorn app.main:app --host 0.0.0.0 --port 8000