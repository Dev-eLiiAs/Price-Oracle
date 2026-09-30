FROM python:3.12-slim

WORKDIR /app

COPY backend/pyproject.toml ./backend/pyproject.toml
RUN pip install --no-cache-dir --upgrade pip \
    && pip install --no-cache-dir "./backend[dev]"

COPY backend/app ./app
COPY worker ./worker

ENV PYTHONPATH=/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]
