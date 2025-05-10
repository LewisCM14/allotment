#!/bin/sh
set -e

# Replace environment variables in the Nginx config
envsubst '${VITE_API_URL}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

# Execute the main container command
exec "$@"
