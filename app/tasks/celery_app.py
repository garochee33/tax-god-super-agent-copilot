"""
Celery application bootstrap for Tax God background processing.
"""

from __future__ import annotations

from celery import Celery

from app.core.config import get_settings

settings = get_settings()

celery_app = Celery(
    "tax_god",
    broker=settings.CELERY_BROKER_URL,
    backend=settings.CELERY_RESULT_BACKEND,
    include=["app.tasks.ops_tasks"],
)

celery_app.conf.update(
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    task_track_started=True,
    worker_prefetch_multiplier=1,
    task_acks_late=True,
    result_expires=3600,
    beat_schedule={
        "refresh-integration-tokens-every-15-min": {
            "task": "app.tasks.ops_tasks.refresh_integration_tokens",
            "schedule": 15 * 60,
        },
        "budget-guard-every-5-min": {
            "task": "app.tasks.ops_tasks.budget_guard_watchdog",
            "schedule": 5 * 60,
        },
        "regulatory-heartbeat-every-60-min": {
            "task": "app.tasks.ops_tasks.regulatory_scan_heartbeat",
            "schedule": 60 * 60,
        },
    },
)
