from celery import Celery
from app.core.config import settings
import os

# Create Celery instance
celery_app = Celery(
    "ai-automation-workers",
    broker=settings.REDIS_URL,
    backend=settings.REDIS_URL,
    include=[
        "app.tasks.runner",
        "app.tasks.connector_executor",
        "app.tasks.scheduler",
        "app.tasks.webhook_ingress",
        "app.tasks.simulator",
        "app.tasks.mapper",
        "app.tasks.monitor",
        "app.tasks.exporter",
    ]
)

# Celery configuration
celery_app.conf.update(
    task_serializer="json",
    accept_content=["json"],
    result_serializer="json",
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    task_time_limit=30 * 60,  # 30 minutes
    task_soft_time_limit=25 * 60,  # 25 minutes
    worker_prefetch_multiplier=settings.WORKERS_PREFETCH_MULTIPLIER,
    task_acks_late=settings.WORKERS_TASK_ACKS_LATE,
    task_reject_on_worker_lost=settings.WORKERS_TASK_REJECT_ON_WORKER_LOST,
    worker_concurrency=settings.WORKERS_CONCURRENCY,
    worker_max_tasks_per_child=1000,
    worker_max_memory_per_child=200000,  # 200MB
    result_expires=3600,  # 1 hour
    task_routes={
        "app.tasks.runner.*": {"queue": "runner"},
        "app.tasks.connector_executor.*": {"queue": "connector"},
        "app.tasks.scheduler.*": {"queue": "scheduler"},
        "app.tasks.webhook_ingress.*": {"queue": "webhook"},
        "app.tasks.simulator.*": {"queue": "simulator"},
        "app.tasks.mapper.*": {"queue": "mapper"},
        "app.tasks.monitor.*": {"queue": "monitor"},
        "app.tasks.exporter.*": {"queue": "exporter"},
    },
    task_default_queue="default",
    task_default_exchange="default",
    task_default_routing_key="default",
)

if __name__ == "__main__":
    celery_app.start()
