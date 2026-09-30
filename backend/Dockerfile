FROM mcr.microsoft.com/playwright/python:v1.48.0-jammy

WORKDIR /app

COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "./backend[dev]"

COPY backend/app ./app
COPY backend/alembic.ini ./alembic.ini
COPY backend/alembic ./alembic
COPY backend/tests ./tests
COPY backend/pytest.ini ./pytest.ini
COPY worker ./worker

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
