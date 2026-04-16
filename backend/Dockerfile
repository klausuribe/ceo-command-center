# ---- Build context is the repo root (see docker-compose.yml) so that
# ----  pyproject.toml and the shared analytics/ai/database/config/etl
# ----  packages are all available for the editable install.
FROM python:3.12-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

# System deps required by psycopg binary and bcrypt
RUN apt-get update \
 && apt-get install -y --no-install-recommends build-essential libpq-dev \
 && rm -rf /var/lib/apt/lists/*

# Install project with backend extras (editable install registers the shared
# packages: analytics, ai, database, config, etl).
COPY pyproject.toml README.md ./
COPY analytics ./analytics
COPY ai ./ai
COPY database ./database
COPY config ./config
COPY etl ./etl
COPY backend ./backend

RUN pip install --upgrade pip \
 && pip install -e ".[backend]"

EXPOSE 8000

CMD ["uvicorn", "backend.app.main:app", "--host", "0.0.0.0", "--port", "8000"]
