FROM python:3.13-alpine as builder

RUN apk add --no-cache bash

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PATH="/root/.local/bin:$PATH"

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync

from python:3.13-alpine as  production

COPY app/prestart.sh .
RUN chmod +x prestart.sh

WORKDIR /app

COPY .env .
COPY . .
COPY --from=builder /app/.venv .venv

ENV PATH="/app/.venv/bin:$PATH"

ENTRYPOINT ["/app/prestart.sh"]
CMD ["uv","run","uvicorn","app.main:create_app"]
#"--host","0.0.0.0","--port","8000","--factory"