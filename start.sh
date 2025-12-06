#!/bin/sh

# Use Render's PORT environment variable, default to 10000
PORT=${PORT:-10000}

# Create nginx config with the correct port
cat > /tmp/nginx.conf << EOF
server {
    listen ${PORT};
    server_name localhost;
    root /var/www/html;
    index index.html;

    gzip on;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml text/javascript;

    location / {
        try_files \$uri \$uri/ /index.html;
    }

    location /api/ {
        rewrite ^/api/(.*) /\$1 break;
        proxy_pass http://127.0.0.1:8000;
        proxy_http_version 1.1;
        proxy_set_header Upgrade \$http_upgrade;
        proxy_set_header Connection 'upgrade';
        proxy_set_header Host \$host;
        proxy_cache_bypass \$http_upgrade;
        proxy_set_header X-Real-IP \$remote_addr;
        proxy_set_header X-Forwarded-For \$proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto \$scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 120s;
    }

    location ~* \.(js|css|png|jpg|jpeg|gif|ico|svg)$ {
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
}
EOF

# Copy config to nginx
cp /tmp/nginx.conf /etc/nginx/conf.d/default.conf

echo "Starting nginx on port ${PORT}..."
nginx -g "daemon off;" &

echo "Starting uvicorn on port 8000..."
exec uvicorn api.main:app --host 0.0.0.0 --port 8000
