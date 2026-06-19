from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.security import get_current_user, require_admin_user
from app.db.models.orders import Order, OrderStatus
from app.db.models.users import User
from app.db.session import get_db
from app.schemas.orders import OrderCreate, OrderRead, OrderStatusUpdate
from app.services.orders import (
    AddressNotFoundError,
    OrderCancellationError,
    OrderStatusUpdateError,
    ProductNotFoundError,
    cancel_order,
    create_order,
    get_order_by_id,
    get_user_order,
    list_user_orders,
    update_order_status,
)


router = APIRouter(prefix="/orders", tags=["orders"])


@router.post("", response_model=OrderRead, status_code=status.HTTP_201_CREATED)
def create_customer_order(
    payload: OrderCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    try:
        return create_order(db, user_id=current_user.id, payload=payload)
    except (AddressNotFoundError, ProductNotFoundError) as exc:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(exc),
        ) from exc


@router.get("", response_model=list[OrderRead])
def list_customer_orders(
    status_filter: OrderStatus | None = Query(default=None, alias="status"),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> list[Order]:
    return list_user_orders(db, user_id=current_user.id, status_filter=status_filter)


@router.get("/{order_id}", response_model=OrderRead)
def read_customer_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    return _get_owned_order(db, user_id=current_user.id, order_id=order_id)


@router.post("/{order_id}/cancel", response_model=OrderRead)
def cancel_customer_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
) -> Order:
    order = _get_owned_order(db, user_id=current_user.id, order_id=order_id)
    try:
        return cancel_order(db, order=order)
    except OrderCancellationError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


@router.patch("/{order_id}/status", response_model=OrderRead)
def update_customer_order_status(
    order_id: int,
    payload: OrderStatusUpdate,
    db: Session = Depends(get_db),
    _: User = Depends(require_admin_user),
) -> Order:
    order = get_order_by_id(db, order_id=order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    try:
        return update_order_status(db, order=order, new_status=payload.status)
    except OrderStatusUpdateError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(exc),
        ) from exc


def _get_owned_order(db: Session, *, user_id: int, order_id: int) -> Order:
    order = get_user_order(db, user_id=user_id, order_id=order_id)
    if order is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Order not found",
        )
    return order
