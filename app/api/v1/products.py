from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.db.models.products import Product
from app.db.session import get_db
from app.schemas.products import ProductRead
from app.services.products import list_active_products


router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(db: Session = Depends(get_db)) -> list[Product]:
    return list_active_products(db)
