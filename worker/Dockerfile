FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "./backend[dev]"

COPY backend/app ./app
COPY worker ./worker

ENV PYTHONPATH=/app

CMD ["celery", "-A", "app.core.celery_app", "worker", "-Q", "scraping,notifications", "--concurrency=2", "--loglevel=info"]
