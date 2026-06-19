from celery import Celery

from app.core.config import settings


celery_app = Celery(
    "order_processing",
    broker=settings.celery_broker_url,
    backend=settings.celery_result_backend,
    include=["app.services.scheduler"],
)

celery_app.conf.update(
    accept_content=["json"],
    beat_schedule={
        "process-pending-orders-every-5-minutes": {
            "task": "app.services.scheduler.process_pending_orders_task",
            "schedule": settings.pending_order_processing_interval_seconds,
        },
    },
    enable_utc=True,
    result_serializer="json",
    task_serializer="json",
    timezone="UTC",
)
