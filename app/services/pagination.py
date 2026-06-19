from typing import TypeVar

from sqlalchemy import Select, func, select
from sqlalchemy.orm import Session

from app.schemas.pagination import PaginatedResponse


T = TypeVar("T")


def paginate_scalars(
    db: Session,
    statement: Select[tuple[T]],
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse[T]:
    total = _count_rows(db, statement)
    offset = (page - 1) * page_size
    items = list(db.scalars(statement.limit(page_size).offset(offset)))
    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def paginate_mappings(
    db: Session,
    statement: Select,
    *,
    page: int,
    page_size: int,
) -> PaginatedResponse[dict]:
    total = _count_rows(db, statement)
    offset = (page - 1) * page_size
    items = [dict(row._mapping) for row in db.execute(statement.limit(page_size).offset(offset))]
    return PaginatedResponse.create(
        items=items,
        page=page,
        page_size=page_size,
        total=total,
    )


def _count_rows(db: Session, statement: Select) -> int:
    count_statement = select(func.count()).select_from(
        statement.order_by(None).limit(None).offset(None).subquery()
    )
    return db.scalar(count_statement) or 0
