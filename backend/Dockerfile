FROM python:3.13-alpine

RUN apk add --no-cache bash

RUN apk add --no-cache postgresql-client

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync

COPY app/prestart.sh .
RUN chmod +x prestart.sh

COPY .env .
COPY . .

ENTRYPOINT ["/app/prestart.sh"]
#CMD ["/app/.venv/bin/uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
CMD ["/app/.venv/bin/gunicorn", "app.main:app", "--workers", "2", "--bind", "0.0.0.0:8000", "--worker-class", "uvicorn.workers.UvicornWorker"]