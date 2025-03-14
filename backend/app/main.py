"""
Application Entrypoint
"""

from fastapi import FastAPI

from app.api.core.config import settings
from app.api.v1 import router as api_router

app = FastAPI(title=settings.APP_NAME, version=settings.APP_VERSION)

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Application Root"""
    return {"message": "Welcome to the Allotment Service API!"}
