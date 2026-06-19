from decimal import Decimal

from sqlalchemy import select
from sqlalchemy.orm import Session, selectinload

from app.db.models.addresses import Address
from app.db.models.orders import Order, OrderItem, OrderStatus
from app.db.models.products import Product
from app.schemas.orders import OrderCreate
from app.services.addresses import get_user_address


MONEY_QUANTUM = Decimal("0.01")


class AddressNotFoundError(ValueError):
    pass


class ProductNotFoundError(ValueError):
    pass


class OrderCancellationError(ValueError):
    pass


def create_order(db: Session, *, user_id: int, payload: OrderCreate) -> Order:
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
        **_shipping_snapshot(address),
        items=order_items,
    )
    db.add(order)
    db.commit()
    db.refresh(order)
    return order


def list_user_orders(
    db: Session,
    *,
    user_id: int,
    status_filter: OrderStatus | None = None,
) -> list[Order]:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.user_id == user_id)
        .order_by(Order.created_at.desc(), Order.id.desc())
    )
    if status_filter is not None:
        statement = statement.where(Order.status == status_filter)
    return list(db.scalars(statement))


def get_user_order(db: Session, *, user_id: int, order_id: int) -> Order | None:
    statement = (
        select(Order)
        .options(selectinload(Order.items))
        .where(Order.id == order_id, Order.user_id == user_id)
    )
    return db.scalar(statement)


def cancel_order(db: Session, *, order: Order) -> Order:
    if order.status != OrderStatus.PENDING:
        raise OrderCancellationError("Only pending orders can be cancelled")

    order.status = OrderStatus.CANCELLED
    db.commit()
    db.refresh(order)
    return order


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
