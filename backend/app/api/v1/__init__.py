from fastapi import APIRouter

from app.api.v1 import (
    family,
    health,
    user,
    user_allotment,
    user_auth,
)

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(user.router, prefix="/users", tags=["User"])
router.include_router(user_auth.router, prefix="/auth", tags=["Auth"])
router.include_router(
    user_allotment.router, prefix="/users/allotment", tags=["User Allotment"]
)
router.include_router(family.router, prefix="/families", tags=["Families"])
