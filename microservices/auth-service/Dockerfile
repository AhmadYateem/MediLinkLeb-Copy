# Multi-stage build for Auth Service
FROM python:3.12-slim as builder

WORKDIR /app

# Install system dependencies
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

# Runtime stage
FROM python:3.12-slim

WORKDIR /app

# Install runtime dependencies only
RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

# Copy installed Python packages from builder
COPY --from=builder /root/.local /root/.local

# Make sure scripts in .local are usable
ENV PATH=/root/.local/bin:$PATH

# Copy application code
COPY . .

# Create directory for static files
RUN mkdir -p staticfiles

# Expose port
EXPOSE 8001

# Environment variable for Django
ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=auth_service.settings

# Run migrations and start Gunicorn
CMD python manage.py migrate --no-input && \
    python manage.py collectstatic --no-input && \
    gunicorn auth_service.wsgi:application --bind 0.0.0.0:8001 --workers 4 --timeout 120
