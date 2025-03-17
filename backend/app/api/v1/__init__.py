from fastapi import APIRouter

from app.api.v1 import health

router = APIRouter()
router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(health.router, prefix="/user", tags=["User"])
