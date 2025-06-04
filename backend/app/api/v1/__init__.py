from fastapi import APIRouter

from app.api.v1 import family, health, user

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(user.router, tags=["Users"])
router.include_router(family.router, prefix="/families", tags=["Families"])
