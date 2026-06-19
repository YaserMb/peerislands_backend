from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from app.db.models.products import Product
from app.db.session import get_db
from app.schemas.pagination import PaginatedResponse
from app.schemas.products import ProductRead
from app.services.products import list_active_products


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=PaginatedResponse[ProductRead])
def list_products(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=20, ge=1, le=100),
    db: Session = Depends(get_db),
) -> PaginatedResponse:
    return list_active_products(db, page=page, page_size=page_size)
