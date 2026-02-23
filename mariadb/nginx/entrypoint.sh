#!/bin/sh
set -e

# Generate htpasswd file at startup from environment variables.
# The file is written to /tmp so the non-root nginx user can always write it.
if [ -z "$NGINX_AUTH_USER" ] || [ -z "$NGINX_AUTH_PASSWORD" ]; then
    echo "ERROR: NGINX_AUTH_USER and NGINX_AUTH_PASSWORD must be set." >&2
    exit 1
fi

htpasswd -bc /tmp/.htpasswd "$NGINX_AUTH_USER" "$NGINX_AUTH_PASSWORD"

exec nginx -g 'daemon off;'
