"""seed sample products

Revision ID: 20260618_0002
Revises: 20260618_0001
Create Date: 2026-06-18
"""

from collections.abc import Sequence
from decimal import Decimal

from alembic import op
import sqlalchemy as sa

revision: str = "20260618_0002"
down_revision: str | None = "20260618_0001"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


sample_products = sa.table(
    "products",
    sa.column("sku", sa.String),
    sa.column("name", sa.String),
    sa.column("description", sa.Text),
    sa.column("price", sa.Numeric(12, 2)),
    sa.column("is_active", sa.Boolean),
)

sample_product_rows = [
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
]


def upgrade() -> None:
    op.bulk_insert(sample_products, sample_product_rows)


def downgrade() -> None:
    op.execute(
        "DELETE FROM products "
        "WHERE sku IN ('PI-KEYBOARD-001', 'PI-MOUSE-001', 'PI-HEADSET-001')"
    )
