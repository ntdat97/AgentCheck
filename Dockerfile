# ===========================================
# AgentCheck Dockerfile
# Multi-stage build for production deployment
# Includes Python backend + React frontend
# ===========================================

# ---- Frontend Build Stage ----
FROM node:20-alpine AS frontend-builder

WORKDIR /app/ui

# Copy package files
COPY ui/package.json ./

# Install dependencies
RUN npm install --silent

# Copy frontend source
COPY ui/ .

# Build for production
RUN npm run build


# ---- Backend Build Stage ----
FROM python:3.11-slim AS backend-builder

# Set working directory
WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first for better caching
COPY requirements.txt .

# Create virtual environment and install dependencies
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
RUN pip install --no-cache-dir --upgrade pip && \
    pip install --no-cache-dir -r requirements.txt


# ---- Production Stage ----
FROM python:3.11-slim AS production

# Labels
LABEL maintainer="AgentCheck Team"
LABEL version="1.0.0"
LABEL description="AI-powered certificate verification system"

# Create non-root user for security
RUN groupadd -r agentcheck && useradd -r -g agentcheck agentcheck

# Install nginx for serving frontend
RUN apt-get update && apt-get install -y --no-install-recommends \
    nginx \
    && rm -rf /var/lib/apt/lists/*

# Configure nginx to run as non-root
RUN mkdir -p /var/lib/nginx/body /var/lib/nginx/proxy /var/lib/nginx/fastcgi \
             /var/lib/nginx/uwsgi /var/lib/nginx/scgi \
             /var/run /var/log/nginx \
    && chown -R agentcheck:agentcheck /var/lib/nginx /var/run /var/log/nginx /var/www/html /etc/nginx/conf.d \
    && chmod -R 755 /var/lib/nginx /var/run /var/log/nginx /etc/nginx/conf.d \
    && sed -i 's/user www-data;/# user www-data;/' /etc/nginx/nginx.conf \
    && sed -i 's|pid /run/nginx.pid;|pid /tmp/nginx.pid;|' /etc/nginx/nginx.conf

# Set working directory
WORKDIR /app

# Copy virtual environment from builder
COPY --from=backend-builder /opt/venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"

# Copy frontend build
COPY --from=frontend-builder /app/ui/dist /var/www/html

# Copy nginx configuration
COPY nginx.conf /etc/nginx/conf.d/default.conf

# Copy application code
COPY --chown=agentcheck:agentcheck api/ ./api/
COPY --chown=agentcheck:agentcheck config/ ./config/

# Create data directories (not copied from repo as they're gitignored)
RUN mkdir -p /app/data/outbox \
             /app/data/inbox \
             /app/data/reports \
             /app/data/audit_logs \
             /app/data/uploads \
             /app/data/queue \
    && chown -R agentcheck:agentcheck /app/data

# Set environment variables
ENV PYTHONUNBUFFERED=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV DATA_DIR=/app/data
ENV CONFIG_DIR=/app/config

# Expose port 10000 (Render's default port)
EXPOSE 10000

# Copy startup script
COPY --chown=agentcheck:agentcheck start.sh /app/start.sh
RUN chmod +x /app/start.sh

# Switch to non-root user
USER agentcheck

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/health')" || exit 1

# Default command - use startup script
CMD ["/app/start.sh"]


# ---- Development Stage ----
FROM production AS development

# Switch back to root for dev dependencies
USER root

# Install development dependencies
RUN pip install --no-cache-dir pytest pytest-asyncio pytest-cov black isort mypy

# Switch back to non-root user
USER agentcheck

# Development command with hot reload
CMD ["uvicorn", "api.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
