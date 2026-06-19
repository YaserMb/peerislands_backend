from datetime import datetime
from decimal import Decimal

from pydantic import BaseModel, ConfigDict, Field

from app.db.models.orders import OrderStatus


class OrderItemCreate(BaseModel):
    product_id: int = Field(gt=0)
    quantity: int = Field(gt=0)


class OrderCreate(BaseModel):
    shipping_address_id: int = Field(gt=0)
    items: list[OrderItemCreate] = Field(min_length=1)


class OrderStatusUpdate(BaseModel):
    status: OrderStatus


class OrderItemRead(BaseModel):
    id: int
    product_id: int
    product_name: str
    quantity: int
    unit_price: Decimal
    line_total: Decimal

    model_config = ConfigDict(from_attributes=True)


class OrderReportRead(BaseModel):
    id: int
    user_id: int
    customer_email: str
    status: OrderStatus
    total_amount: Decimal
    item_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class OrderRead(BaseModel):
    id: int
    user_id: int
    shipping_address_id: int
    status: OrderStatus
    total_amount: Decimal
    shipping_full_name: str
    shipping_phone: str
    shipping_address_line1: str
    shipping_address_line2: str | None
    shipping_city: str
    shipping_state: str
    shipping_postal_code: str
    shipping_country: str
    items: list[OrderItemRead]
    created_at: datetime
    updated_at: datetime

    model_config = ConfigDict(from_attributes=True)
