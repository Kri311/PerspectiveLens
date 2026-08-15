import os
import logging
import requests
from celery import Celery
from celery.schedules import crontab

logger = logging.getLogger(__name__)

REDIS_URL = os.getenv("REDIS_URL", "redis://redis:6379/0")

celery_app = Celery(
    "analysis_worker",
    broker=REDIS_URL,
    backend=REDIS_URL,
    include=['app.tasks']
)

celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="Asia/Kolkata",
    enable_utc=True,
    task_routes={
        'app.tasks.*': {'queue': 'analysis'}
    }
)

celery_app.conf.beat_schedule = {
    'process-queued-articles-every-15-secs': {
        'task': 'app.tasks.process_queued_articles',
        'schedule': 15.0,
    },
}

if __name__ == '__main__':
    celery_app.start()
