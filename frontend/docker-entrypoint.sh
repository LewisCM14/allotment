#!/bin/sh
set -e

# Check if VITE_API_URL is set, use default if not
if [ -z "$VITE_API_URL" ]; then
  echo "WARNING: VITE_API_URL is not set. Using default API URL."
  export VITE_API_URL="http://localhost:3000"
fi

# Extract hostname from API URL for proper headers
export VITE_API_URL_HOST=$(echo $VITE_API_URL | sed -e 's|^[^/]*//||' -e 's|/.*$||')

# Verify extraction worked correctly
if [ -z "$VITE_API_URL_HOST" ]; then
  echo "ERROR: Failed to extract host from VITE_API_URL. Check the format of your API URL."
  exit 1
fi

echo "Configuring Nginx with API URL: $VITE_API_URL (Host: $VITE_API_URL_HOST)"

# Replace environment variables in the Nginx config
envsubst '${VITE_API_URL} ${VITE_API_URL_HOST}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Nginx configuration successfully generated."

# Execute the main container command
exec "$@"
