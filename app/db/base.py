from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


# Import model modules so Alembic can discover tables through Base.metadata.
from app.db.models import addresses, orders, products, users  # noqa: E402,F401
