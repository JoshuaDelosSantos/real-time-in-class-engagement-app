# syntax=docker/dockerfile:1.6

FROM python:3.11-slim-bookworm AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
  PIP_DISABLE_PIP_VERSION_CHECK=1 \
  PYTHONPATH="/app/backend:/app"

WORKDIR /app/backend

# Copy dependency definitions and install requirements.
COPY backend/requirements.txt ./

RUN pip install --no-cache-dir --upgrade pip && \
    if [ -f requirements.txt ]; then \
      pip install --no-cache-dir -r requirements.txt; \
    fi

# Copy application source (allowing docker compose to mount for development reloads).
COPY backend/app ./app

# Copy frontend static assets for serving via FastAPI.
RUN mkdir -p /app/frontend/public
COPY frontend/public /app/frontend/public

EXPOSE 8000

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
