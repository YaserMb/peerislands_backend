import hashlib
import json
from decimal import Decimal

from sqlalchemy import func, select, update
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, selectinload

from app.db.models.addresses import Address
from app.db.models.orders import Order, OrderItem, OrderStatus
from app.db.models.products import Product
from app.db.models.users import User
from app.schemas.pagination import PaginatedResponse
from app.schemas.orders import OrderCreate
from app.services.addresses import get_user_address
from app.services.pagination import paginate_mappings, paginate_scalars


MONEY_QUANTUM = Decimal("0.01")
VALID_ORDER_STATUS_TRANSITIONS: dict[OrderStatus, set[OrderStatus]] = {
    OrderStatus.PENDING: {OrderStatus.PROCESSING, OrderStatus.CANCELLED},
    OrderStatus.PROCESSING: {OrderStatus.SHIPPED},
    OrderStatus.SHIPPED: {OrderStatus.DELIVERED},
    OrderStatus.DELIVERED: set(),
    OrderStatus.CANCELLED: set(),
}


class AddressNotFoundError(ValueError):
    pass


class ProductNotFoundError(ValueError):
    pass


class OrderCancellationError(ValueError):
    pass


class OrderStatusUpdateError(ValueError):
    pass


class OrderIdempotencyConflictError(ValueError):
    pass


def create_order(
    db: Session,
    *,
    user_id: int,
    payload: OrderCreate,
    idempotency_key: str | None = None,
) -> Order:
    payload_hash = _idempotency_payload_hash(payload) if idempotency_key else None
    if idempotency_key is not None:
        existing_order = get_order_by_idempotency_key(
            db,
            user_id=user_id,
            idempotency_key=idempotency_key,
        )
        if existing_order is not None:
            _validate_idempotency_payload(existing_order, payload_hash)
            return existing_order

    address = get_user_address(
        db,
        user_id=user_id,
        address_id=payload.shipping_address_id,
    )
    if address is None:
        raise AddressNotFoundError("Address not found")

    product_ids = {item.product_id for item in payload.items}
    products = _get_active_products_by_id(db, product_ids)
    missing_product_ids = product_ids.difference(products)
    if missing_product_ids:
        raise ProductNotFoundError("Product not found")

    order_items: list[OrderItem] = []
    total_amount = Decimal("0.00")
    for item in payload.items:
        product = products[item.product_id]
        unit_price = _money(product.price)
        line_total = _money(unit_price * item.quantity)
        total_amount += line_total
        order_items.append(
            OrderItem(
                product_id=product.id,
                product_name=product.name,
                quantity=item.quantity,
                unit_price=unit_price,
                line_total=line_total,
            )
        )

    order = Order(
        user_id=user_id,
        shipping_address_id=address.id,
        status=OrderStatus.PENDING,
        total_amount=_money(total_amount),
        idempotency_key=idempotency_key,
        idempotency_payload_hash=payload_hash,
        **_shipping_snapshot(address),
        items=order_items,
    )
    db.add(order)
    try:
        db.commit()
    except IntegrityError:
        db.rollback()
        if idempotency_key is not None:
            existing_order = get_order_by_idempotency_key(
                db,
                user_id=user_id,
                idempotency_key=idempotency_key,
            )
            if existing_order is not None:
                _validate_idempotency_payload(existing_order, payload_hash)
                return existing_order
        raise

    db.refresh(order)
    return order


def list_user_orders(
    db: Session,
    *,
    user_id: int,
    page: int,
    page_size: int,
    status_filter: OrderStatus | None = None,
) -> PaginatedResponse:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)
    return paginate_scalars(db, statement, page=page, page_size=page_size)


def get_user_order(db: Session, *, user_id: int, order_id: int) -> Order | None:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    return db.scalar(statement)


def get_order_by_id(db: Session, *, order_id: int) -> Order | None:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id)
    )
    return db.scalar(statement)


def get_order_by_idempotency_key(
    db: Session,
    *,
    user_id: int,
    idempotency_key: str,
) -> Order | None:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id, Order.idempotency_key == idempotency_key)
    )
    return db.scalar(statement)


def list_all_orders_report(
    db: Session,
    *,
    page: int,
    page_size: int,
    status_filter: OrderStatus | None = None,
) -> PaginatedResponse:
    statement = (
        select(
            Order.id,
            Order.user_id,
            User.email.label("customer_email"),
            Order.status,
            Order.total_amount,
            func.count(OrderItem.id).label("item_count"),
            Order.created_at,
        )
        .join(User, Order.user_id == User.id)
        .join(OrderItem, OrderItem.order_id == Order.id)
        .group_by(
            Order.id,
            Order.user_id,
            User.email,
            Order.status,
            Order.total_amount,
            Order.created_at,
        )
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)

    return paginate_mappings(db, statement, page=page, page_size=page_size)


def update_order_status(db: Session, *, order: Order, new_status: OrderStatus) -> Order:
    if order.status == new_status:
        return order
    if new_status == OrderStatus.CANCELLED:
        raise OrderStatusUpdateError("Use the cancel endpoint to cancel pending orders")
    if new_status not in VALID_ORDER_STATUS_TRANSITIONS[order.status]:
        raise OrderStatusUpdateError(
            f"Invalid order status transition from {order.status.value} to {new_status.value}"
        )

    order.status = new_status
    db.commit()
    db.refresh(order)
    return order


def cancel_order(db: Session, *, order: Order) -> Order:
    if OrderStatus.CANCELLED not in VALID_ORDER_STATUS_TRANSITIONS[order.status]:
        raise OrderCancellationError("Only pending orders can be cancelled")

    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


def process_pending_orders(db: Session) -> int:
    statement = (
        update(Order)
        .where(Order.status == OrderStatus.PENDING)
        .values(status=OrderStatus.PROCESSING, updated_at=func.now())
    )
    result = db.execute(statement)
    db.commit()
    return result.rowcount or 0


def _get_active_products_by_id(db: Session, product_ids: set[int]) -> dict[int, Product]:
    statement = select(Product).where(
        Product.id.in_(product_ids),
        Product.is_active.is_(True),
    )
    return {product.id: product for product in db.scalars(statement)}


def _shipping_snapshot(address: Address) -> dict[str, str | None]:
    return {
        "shipping_full_name": address.full_name,
        "shipping_phone": address.phone,
        "shipping_address_line1": address.address_line1,
        "shipping_address_line2": address.address_line2,
        "shipping_city": address.city,
        "shipping_state": address.state,
        "shipping_postal_code": address.postal_code,
        "shipping_country": address.country,
    }


def _money(value: Decimal) -> Decimal:
    return value.quantize(MONEY_QUANTUM)


def _idempotency_payload_hash(payload: OrderCreate) -> str:
    serialized_payload = json.dumps(
        payload.model_dump(mode="json"),
        separators=(",", ":"),
        sort_keys=True,
    )
    return hashlib.sha256(serialized_payload.encode("utf-8")).hexdigest()


def _validate_idempotency_payload(order: Order, payload_hash: str | None) -> None:
    if order.idempotency_payload_hash != payload_hash:
        raise OrderIdempotencyConflictError(
            "Idempotency key was already used with a different order payload"
        )
