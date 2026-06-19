"""add order idempotency

Revision ID: 20260619_0003
Revises: 20260618_0002
Create Date: 2026-06-19
"""

from collections.abc import Sequence

from alembic import op
import sqlalchemy as sa

revision: str = "20260619_0003"
down_revision: str | None = "20260618_0002"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.add_column(
            sa.Column("idempotency_key", sa.String(length=255), nullable=True)
        )
        batch_op.add_column(
            sa.Column("idempotency_payload_hash", sa.String(length=64), nullable=True)
        )
        batch_op.create_unique_constraint(
            "uq_orders_user_id_idempotency_key",
            ["user_id", "idempotency_key"],
        )


def downgrade() -> None:
    with op.batch_alter_table("orders") as batch_op:
        batch_op.drop_constraint("uq_orders_user_id_idempotency_key", type_="unique")
        batch_op.drop_column("idempotency_payload_hash")
        batch_op.drop_column("idempotency_key")
