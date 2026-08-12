"""Celery application configuration."""
from celery import Celery
from celery.schedules import crontab
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
    beat_schedule={
        # Daily IPO discovery at 6 AM UTC
        "daily-ipo-discovery": {
            "task": "app.agents.analysis.tasks.scheduled_ipo_discovery",
            "schedule": crontab(hour=6, minute=0),
        },
        # Daily Indian IPO discovery at 7 AM UTC
        "daily-ipo-discovery-india": {
            "task": "app.agents.analysis.tasks.scheduled_ipo_discovery_india",
            "schedule": crontab(hour=7, minute=0),
        },
        # Daily reflection cycle at 2 AM UTC
        "daily-reflection": {
            "task": "app.agents.analysis.tasks.scheduled_reflection",
            "schedule": crontab(hour=2, minute=0),
        },
        # Data refresh every 4 hours
        "data-refresh": {
            "task": "app.agents.analysis.tasks.scheduled_data_refresh",
            "schedule": crontab(minute=0, hour="*/4"),
        },
        # Job cleanup daily at 3 AM UTC
        "job-cleanup": {
            "task": "app.agents.analysis.tasks.cleanup_old_jobs",
            "schedule": crontab(hour=3, minute=0),
        },
    },
)

celery_app.autodiscover_tasks()