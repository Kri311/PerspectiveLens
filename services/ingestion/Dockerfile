FROM python:3.11-slim

WORKDIR /app

# Install system dependencies required for fasttext and psycopg2
RUN apt-get update && apt-get install -y \
    build-essential \
    libpq-dev \
    wget \
    && rm -rf /var/lib/apt/lists/*

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Download fastText language identification model
RUN mkdir -p /app/models && \
    wget -O /app/models/lid.176.bin https://dl.fbaipublicfiles.com/fasttext/supervised-models/lid.176.bin

COPY app /app/app

# Set python path
ENV PYTHONPATH=/app

CMD ["celery", "-A", "app.main.celery_app", "worker", "-B", "--loglevel=info"]
