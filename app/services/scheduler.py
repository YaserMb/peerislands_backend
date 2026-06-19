from app.core.celery_app import celery_app
from app.core.config import settings
from app.db.session import SessionLocal
from app.services.locks import redis_distributed_lock
from app.services.orders import process_pending_orders


PENDING_ORDER_PROCESSING_LOCK_KEY = "locks:pending-order-processing"


@celery_app.task(name="app.services.scheduler.process_pending_orders_task")
def process_pending_orders_task() -> int:
    db = SessionLocal()
    try:
        with redis_distributed_lock(
            redis_url=settings.celery_broker_url,
            key=PENDING_ORDER_PROCESSING_LOCK_KEY,
            ttl_seconds=settings.pending_order_processing_lock_ttl_seconds,
        ) as acquired:
            if not acquired:
                return 0
            return process_pending_orders(db)
    finally:
        db.close()
