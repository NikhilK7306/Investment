"""Celery application configuration."""
from celery import Celery
from app.core.config.settings import get_settings

settings = get_settings()

celery_app = Celery(
    "ipo_intelligence",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=[
        "app.agents.discovery.tasks",
        "app.agents.collection.tasks",
        "app.agents.analysis.tasks",
        "app.agents.report.tasks",
        "app.memory.tasks",
        "app.reflection.tasks",
    ],
)

celery_app.conf.update(
    task_serializer=settings.celery_task_serializer,
    result_serializer=settings.celery_result_serializer,
    accept_content=settings.celery_accept_content,
    timezone=settings.celery_timezone,
    enable_utc=settings.celery_enable_utc,
    task_track_started=settings.celery_task_track_started,
    task_time_limit=settings.celery_task_time_limit,
    worker_prefetch_multiplier=settings.celery_worker_prefetch_multiplier,
    worker_max_tasks_per_child=settings.celery_worker_max_tasks_per_child,
    beat_schedule={},
)

celery_app.autodiscover_tasks()