# Multi-stage optimized Dockerfile for AgriYield AI Engine
FROM python:3.11-slim as builder

WORKDIR /app

# Install build dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copy and install python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Final runtime image
FROM python:3.11-slim

WORKDIR /app

# Create non-root app user for security
RUN groupadd -g 1000 appgroup && \
    useradd -u 1000 -g appgroup -m -s /bin/sh appuser && \
    mkdir -p /home/appuser && \
    chown -R appuser:appgroup /home/appuser

# Copy installed python dependencies from builder stage
COPY --from=builder /install /usr/local

# Copy application files
COPY . /app

# Set ownership
RUN chown -R appuser:appgroup /app

USER appuser

# Environment defaults
ENV PORT=5000 \
    HOST=0.0.0.0 \
    HOME=/home/appuser \
    PYTHONUNBUFFERED=1 \
    FLASK_ENV=production

EXPOSE 5000

# Healthcheck configuration
HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/api/health')" || exit 1

# Production WSGI server launch
CMD ["gunicorn", "--bind", "0.0.0.0:5000", "--workers", "1", "--threads", "4", "--preload", "--timeout", "120", "app:app"]
