FROM python:3.10-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt-get/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY app/ ./app/
COPY ml/ ./ml/
COPY dataset/ ./dataset/
COPY models/ ./models/

EXPOSE 8000


CMD ["uvicorn", "app.main:app", "--host", "localhost", "--port", "8000"]