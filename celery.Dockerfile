FROM python:3.10.5-slim

ENV PYTHONUNBUFFERED 1

WORKDIR /app


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY . .


CMD ["celery", "-A", "make_celery", "worker", "--loglevel=info"]