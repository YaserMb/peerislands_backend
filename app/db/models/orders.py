from __future__ import annotations

from datetime import datetime
from decimal import Decimal
from enum import Enum
from typing import TYPE_CHECKING

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, Numeric, String, UniqueConstraint, func
from sqlalchemy import Enum as SQLEnum
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.db.models.addresses import Address
    from app.db.models.products import Product
    from app.db.models.users import User


class OrderStatus(str, Enum):
    PENDING = "PENDING"
    PROCESSING = "PROCESSING"
    SHIPPED = "SHIPPED"
    DELIVERED = "DELIVERED"
    CANCELLED = "CANCELLED"


class Order(Base):
    __tablename__ = "orders"
    __table_args__ = (
        CheckConstraint("total_amount >= 0", name="ck_orders_total_amount_non_negative"),
        UniqueConstraint("user_id", "idempotency_key", name="uq_orders_user_id_idempotency_key"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id"), index=True, nullable=False)
    shipping_address_id: Mapped[int] = mapped_column(
        ForeignKey("addresses.id"),
        index=True,
        nullable=False,
    )
    status: Mapped[OrderStatus] = mapped_column(
        SQLEnum(OrderStatus, name="order_status", native_enum=False),
        default=OrderStatus.PENDING,
        index=True,
        nullable=False,
    )
    total_amount: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    idempotency_key: Mapped[str | None] = mapped_column(String(255), nullable=True)
    idempotency_payload_hash: Mapped[str | None] = mapped_column(String(64), nullable=True)
    shipping_full_name: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_phone: Mapped[str] = mapped_column(String(32), nullable=False)
    shipping_address_line1: Mapped[str] = mapped_column(String(255), nullable=False)
    shipping_address_line2: Mapped[str | None] = mapped_column(String(255), nullable=True)
    shipping_city: Mapped[str] = mapped_column(String(120), nullable=False)
    shipping_state: Mapped[str] = mapped_column(String(120), nullable=False)
    shipping_postal_code: Mapped[str] = mapped_column(String(32), nullable=False)
    shipping_country: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    user: Mapped[User] = relationship("User", back_populates="orders")
    shipping_address: Mapped[Address] = relationship("Address", back_populates="orders")
    items: Mapped[list[OrderItem]] = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
    )


class OrderItem(Base):
    __tablename__ = "order_items"
    __table_args__ = (
        CheckConstraint("quantity > 0", name="ck_order_items_quantity_positive"),
        CheckConstraint("unit_price >= 0", name="ck_order_items_unit_price_non_negative"),
        CheckConstraint("line_total >= 0", name="ck_order_items_line_total_non_negative"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    order_id: Mapped[int] = mapped_column(ForeignKey("orders.id"), index=True, nullable=False)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id"), index=True, nullable=False)
    product_name: Mapped[str] = mapped_column(String(255), nullable=False)
    quantity: Mapped[int] = mapped_column(nullable=False)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)
    line_total: Mapped[Decimal] = mapped_column(Numeric(12, 2), nullable=False)

    order: Mapped[Order] = relationship("Order", back_populates="items")
    product: Mapped[Product] = relationship("Product", back_populates="order_items")
