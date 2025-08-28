FROM python:3.13-slim-bookworm

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /celery


COPY pyproject.toml .
COPY uv.lock .

RUN uv sync

COPY /infrastructure/celery .