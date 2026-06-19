from app.core.celery_app import celery_app
from app.db.session import SessionLocal
from app.services.orders import process_pending_orders


@celery_app.task(name="app.services.scheduler.process_pending_orders_task")
def process_pending_orders_task() -> int:
    db = SessionLocal()
    try:
        return process_pending_orders(db)
    finally:
        db.close()
