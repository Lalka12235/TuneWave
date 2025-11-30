FROM python:3.13-alpine

RUN apk add --no-cache bash

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

COPY uv.lock pyproject.toml ./

RUN uv sync

COPY app/prestart.sh .
RUN chmod +x prestart.sh

COPY .env .
COPY . .

ENTRYPOINT ["/app/prestart.sh"]
CMD ["uv","run","uvicorn","app.main:create_app","--host","0.0.0.0","--port","8000","--factory"]