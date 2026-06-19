from math import ceil
from typing import Generic, TypeVar

from pydantic import BaseModel, Field


T = TypeVar("T")


class PaginatedResponse(BaseModel, Generic[T]):
    items: list[T]
    page: int = Field(ge=1)
    page_size: int = Field(ge=1)
    total: int = Field(ge=0)
    total_pages: int = Field(ge=0)

    @classmethod
    def create(
        cls,
        *,
        items: list[T],
        page: int,
        page_size: int,
        total: int,
    ) -> "PaginatedResponse[T]":
        return cls(
            items=items,
            page=page,
            page_size=page_size,
            total=total,
            total_pages=ceil(total / page_size) if total else 0,
        )
