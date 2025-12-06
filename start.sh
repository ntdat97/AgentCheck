#!/bin/sh

# Start nginx in background
echo "Starting nginx on port 10000..."
nginx

# Check if nginx started successfully
sleep 1
if ! pgrep -x nginx > /dev/null; then
    echo "ERROR: nginx failed to start"
    exit 1
fi

echo "nginx started successfully"
echo "Starting uvicorn on port 8000..."

# Start uvicorn in foreground (this keeps the container running)
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
