from decimal import Decimal
from typing import TypedDict

from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.models.products import Product
from app.schemas.pagination import PaginatedResponse
from app.services.pagination import paginate_scalars


class SampleProduct(TypedDict):
    sku: str
    name: str
    description: str
    price: Decimal
    is_active: bool


SAMPLE_PRODUCTS: tuple[SampleProduct, ...] = (
    {
        "sku": "PI-KEYBOARD-001",
        "name": "Mechanical Keyboard",
        "description": "Compact mechanical keyboard with hot-swappable switches.",
        "price": Decimal("79.99"),
        "is_active": True,
    },
    {
        "sku": "PI-MOUSE-001",
        "name": "Wireless Mouse",
        "description": "Ergonomic wireless mouse with adjustable DPI.",
        "price": Decimal("29.99"),
        "is_active": True,
    },
    {
        "sku": "PI-HEADSET-001",
        "name": "Noise-Cancelling Headset",
        "description": "Over-ear headset with active noise cancellation.",
        "price": Decimal("119.99"),
        "is_active": True,
    },
)


def list_active_products(db: Session, *, page: int, page_size: int) -> PaginatedResponse:
    statement = select(Product).where(Product.is_active.is_(True)).order_by(Product.id)
    return paginate_scalars(db, statement, page=page, page_size=page_size)


def get_active_product_by_id(db: Session, product_id: int) -> Product | None:
    statement = select(Product).where(
        Product.id == product_id,
        Product.is_active.is_(True),
    )
    return db.scalar(statement)


def seed_sample_products(db: Session) -> list[Product]:
    skus = [product["sku"] for product in SAMPLE_PRODUCTS]
    existing_skus = set(db.scalars(select(Product.sku).where(Product.sku.in_(skus))))

    products = [
        Product(**product)
        for product in SAMPLE_PRODUCTS
        if product["sku"] not in existing_skus
    ]
    if products:
        db.add_all(products)
        db.commit()
        for product in products:
            db.refresh(product)

    return list(db.scalars(select(Product).where(Product.sku.in_(skus)).order_by(Product.id)))
