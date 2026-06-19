from fastapi import FastAPI
from starlette.requests import Request

from app.api.v1.api import api_router
from app.core.config import settings
from app.core.logging import get_logger, setup_logging


setup_logging()
logger = get_logger("app.main")

app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(api_router)


@app.middleware("http")
async def log_unhandled_errors(request: Request, call_next):
    try:
        return await call_next(request)
    except Exception:
        logger.exception(
            "Unhandled error while processing %s %s",
            request.method,
            request.url.path,
        )
        raise


@app.get('/test')
def main():
    return 'yaser'
