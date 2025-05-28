from fastapi import APIRouter

from app.api.v1 import family, health, user

router = APIRouter()

router.include_router(health.router, prefix="/health")
router.include_router(user.router)
router.include_router(family.router)
