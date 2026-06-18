from fastapi import FastAPI

from app.api.v1.api import api_router
from app.core.config import settings


app = FastAPI(title=settings.app_name, debug=settings.debug)
app.include_router(api_router)


@app.get('/test')
def main():
    return 'yaser'
