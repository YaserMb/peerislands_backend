from fastapi import APIRouter

from app.api.v1.addresses import router as addresses_router
from app.api.v1.auth import router as auth_router
from app.api.v1.orders import router as orders_router
from app.api.v1.products import router as products_router
from app.api.v1.reports import router as reports_router


api_router = APIRouter(prefix="/api/v1")
api_router.include_router(addresses_router)
api_router.include_router(auth_router)
api_router.include_router(orders_router)
api_router.include_router(products_router)
api_router.include_router(reports_router)
