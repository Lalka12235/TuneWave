FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY ./infrastructure/celery/pyproject.toml ./infrastructure/celery/
COPY ./infrastructure/celery/uv.lock ./infrastructure/celery/

WORKDIR /app/infrastructure/celery

RUN uv sync

WORKDIR /app

COPY . .

CMD ["celery", "-A", "infrastructure.celery.celery.celery_app", "worker", "--loglevel=info"]