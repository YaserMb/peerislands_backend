from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.core.security import require_admin_user
from app.db.models.orders import OrderStatus
from app.db.models.users import User
from app.db.session import get_db
from app.schemas.orders import OrderReportRead
from app.schemas.pagination import PaginatedResponse
from app.services.orders import list_all_orders_report


router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/orders", response_model=PaginatedResponse[OrderReportRead])
def list_orders_report(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_user),
) -> PaginatedResponse:
    return list_all_orders_report(
        db,
        page=page,
        page_size=page_size,
        status_filter=status_filter,
    )
