FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock .
COPY pyproject.toml .

RUN uv sync

COPY ./app ./app
COPY ./infrastructure ./infrastructure

CMD ["celery", "-A", "infrastructure.celery.celery.celery_app", "worker", "--loglevel=info"]