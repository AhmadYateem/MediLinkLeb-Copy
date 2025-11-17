FROM python:3.12-slim as builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential libpq-dev && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir --user -r requirements.txt

FROM python:3.12-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 && rm -rf /var/lib/apt/lists/*

COPY --from=builder /root/.local /root/.local
ENV PATH=/root/.local/bin:$PATH

COPY . .
RUN mkdir -p staticfiles

EXPOSE 8003

ENV PYTHONUNBUFFERED=1 \
    DJANGO_SETTINGS_MODULE=patient_service.settings

CMD python manage.py migrate --no-input && \
    python manage.py collectstatic --no-input && \
    gunicorn patient_service.wsgi:application --bind 0.0.0.0:8003 --workers 4 --timeout 120
