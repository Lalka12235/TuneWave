FROM python:3.13-alpine

WORKDIR /app

RUN apk add --no-cache bash

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app/prestart.sh .
RUN chmod +x prestart.sh

COPY .env .
COPY . .

ENTRYPOINT ["/app/prestart.sh"]
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
