from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin_user
from app.db.models.orders import OrderStatus
from app.db.models.users import User
from app.db.session import get_db
from app.schemas.orders import OrderReportRead
from app.services.orders import list_all_orders_report


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/orders", response_model=list[OrderReportRead])
def list_orders_report(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_user),
) -> list[dict]:
    return list_all_orders_report(db, status_filter=status_filter)
