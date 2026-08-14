#!/bin/sh
# Docker entrypoint for frontend
# Handles:
# 1. Runtime BACKEND_URL substitution for Cloud Run deployments
# 2. Dynamic PORT configuration for Cloud Run

set -e

# Set default port (Cloud Run typically sets PORT env var)
PORT=${PORT:-80}

echo "🚀 Starting frontend (port: $PORT, backend: ${BACKEND_URL:-/api})"

# If BACKEND_URL is provided, substitute it into index.html
if [ -n "$BACKEND_URL" ]; then
  echo "🔧 Configuring frontend with backend URL: $BACKEND_URL"
  
  # Replace ${BACKEND_URL} placeholder in index.html with actual URL
  sed "s|'\${BACKEND_URL}'|'$BACKEND_URL'|g" /usr/share/nginx/html/index.html > /tmp/index.html.tmp
  mv /tmp/index.html.tmp /usr/share/nginx/html/index.html
else
  echo "ℹ️  Using default backend URL (/api - dev/proxy mode)"
  sed "s|'\${BACKEND_URL}'|''|g" /usr/share/nginx/html/index.html > /tmp/index.html.tmp
  mv /tmp/index.html.tmp /usr/share/nginx/html/index.html
fi

# Update nginx config to use dynamic PORT
sed -i "s/listen 80/listen $PORT/" /etc/nginx/conf.d/default.conf

# Execute remaining arguments (nginx command)
exec "$@"
