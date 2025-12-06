#!/bin/sh

# Start nginx in background
# Default to port 10000 if not set
PORT="${PORT:-10000}"
API_PORT="${API_PORT:-8000}"

# Start nginx in background
echo "Starting nginx on port $PORT..."

# Update nginx config to listen on the correct port
sed -i "s/listen 10000;/listen $PORT;/g" /etc/nginx/conf.d/default.conf

nginx

# Check if nginx started successfully
sleep 1
if ! pgrep -x nginx > /dev/null; then
    echo "ERROR: nginx failed to start"
    exit 1
fi

echo "nginx started successfully"
echo "Starting uvicorn on port $API_PORT..."

# Start uvicorn in foreground (this keeps the container running)
exec uvicorn api.main:app --host 0.0.0.0 --port $API_PORT
