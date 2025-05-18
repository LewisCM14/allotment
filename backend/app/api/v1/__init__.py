from fastapi import APIRouter

from app.api.v1 import health, user

router = APIRouter()

router.include_router(health.router, prefix="/health")
router.include_router(user.router)
