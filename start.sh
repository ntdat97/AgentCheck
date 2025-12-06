#!/bin/sh

# Start nginx in background
# Default to port 10000 if not set
PORT="${PORT:-10000}"
API_PORT="${API_PORT:-8000}"

# Start nginx in background
echo "Starting nginx on port $PORT..."

# Update nginx config to listen on the correct port
sed -i "s/listen 10000;/listen $PORT;/g" /etc/nginx/conf.d/default.conf

# Start nginx and capture any errors
if ! nginx 2>&1; then
    echo "ERROR: nginx failed to start"
    echo "Checking nginx configuration..."
    nginx -t 2>&1
    echo "Nginx error log:"
    cat /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
    exit 1
fi

# Give nginx a moment to start
sleep 2

# Check if nginx is running by testing the pidfile
if [ ! -f /tmp/nginx.pid ]; then
    echo "ERROR: nginx failed to start (no pid file)"
    echo "Nginx error log:"
    cat /var/log/nginx/error.log 2>/dev/null || echo "No error log found"
    exit 1
fi

echo "nginx started successfully"
echo "Starting uvicorn on port $API_PORT..."

# Start uvicorn in foreground (this keeps the container running)
exec uvicorn api.main:app --host 0.0.0.0 --port $API_PORT
