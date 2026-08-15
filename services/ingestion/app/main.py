import os
from celery import Celery
from celery.schedules import crontab
import logging

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "ingestion_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks.celery_tasks']
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
)

# Configure Celery Beat scheduler
celery_app.conf.beat_schedule = {
    'fetch-google-news-every-hour': {
        'task': 'app.tasks.celery_tasks.fetch_google_news',
        'schedule': crontab(minute=0), # every hour
    },
    'fetch-newsdata-every-hour': {
        'task': 'app.tasks.celery_tasks.fetch_newsdata_io',
        'schedule': crontab(minute=15), # 15 past the hour
    },
    'fetch-gnews-every-hour': {
        'task': 'app.tasks.celery_tasks.fetch_gnews_io',
        'schedule': crontab(minute=30), # 30 past the hour
    },
    'fetch-currents-every-hour': {
        'task': 'app.tasks.celery_tasks.fetch_currents_api',
        'schedule': crontab(minute=45), # 45 past the hour
    },
}

if __name__ == '__main__':
    celery_app.start()
