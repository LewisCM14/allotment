#!/bin/sh
set -e

# Default Environment Variables
DEFAULT_VITE_APP_TITLE="Allotment"
DEFAULT_VITE_API_VERSION="/api/v1"
DEFAULT_VITE_FORCE_AUTH="false"

# Environment Variables
VITE_APP_TITLE="${VITE_APP_TITLE:-$DEFAULT_VITE_APP_TITLE}"
VITE_API_URL="${VITE_API_URL}"
VITE_API_VERSION="${VITE_API_VERSION:-$DEFAULT_VITE_API_VERSION}"
VITE_CONTACT_EMAIL="${VITE_CONTACT_EMAIL}"
VITE_FORCE_AUTH="${VITE_FORCE_AUTH:-$DEFAULT_VITE_FORCE_AUTH}"

# Create the env-config.js file in a dedicated writable directory (not web root for security)
CONFIG_JS_PATH="/var/cache/nginx/runtime/env-config.js"
echo "Generating $CONFIG_JS_PATH with runtime environment variables..."
cat <<EOF > "$CONFIG_JS_PATH"
window.envConfig = {
  VITE_APP_TITLE: "${VITE_APP_TITLE}",
  VITE_API_URL: "${VITE_API_URL}",
  VITE_API_VERSION: "${VITE_API_VERSION}",
  VITE_CONTACT_EMAIL: "${VITE_CONTACT_EMAIL}",
  VITE_FORCE_AUTH: "${VITE_FORCE_AUTH}"
};
EOF
echo "$CONFIG_JS_PATH generated successfully."

# Export VITE_API_URL so envsubst can use it if it's not already an env var from parent process.
export VITE_API_URL

# Extract hostname from API URL for proper headers
export VITE_API_URL_HOST=$(echo "$VITE_API_URL" | sed -e 's|^[^/]*//||' -e 's|/.*$||')

# Verify extraction worked correctly
if [ -z "$VITE_API_URL_HOST" ]; then
  echo "ERROR: Failed to extract host from VITE_API_URL ($VITE_API_URL). Check the format of your API URL."
  exit 1
fi

echo "Configuring Nginx with API URL: $VITE_API_URL (Host: $VITE_API_URL_HOST)"

# Replace environment variables in the Nginx config
# envsubst will use the exported VITE_API_URL and VITE_API_URL_HOST
envsubst '${VITE_API_URL} ${VITE_API_URL_HOST}' < /etc/nginx/conf.d/default.conf.template > /etc/nginx/conf.d/default.conf

echo "Nginx configuration successfully generated."

# Execute the main container command
exec "$@"
