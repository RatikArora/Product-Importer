"""
Celery application configuration.
"""
import os
from celery import Celery
from app.core.config import settings

# Create Celery app
celery_app = Celery(
    'fulfil_tasks',
    broker=settings.effective_redis_url,
    backend=settings.effective_redis_url,
    include=['app.tasks.import_tasks']
)

# Configure Celery
celery_app.conf.update(
    task_serializer='json',
    accept_content=['json'],
    result_serializer='json',
    timezone='UTC',
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes max per task
    task_soft_time_limit=25 * 60,  # 25 minutes soft limit
    worker_prefetch_multiplier=1,  # One task at a time for memory efficiency
    worker_max_tasks_per_child=10,  # Restart worker after 10 tasks to prevent memory leaks
)

# Make celery_app available as celery for the -A parameter
celery = celery_app
