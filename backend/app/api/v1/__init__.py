from fastapi import APIRouter

from app.api.v1 import (
    auth,
    health,
    registration,
)
from app.api.v1.family import family
from app.api.v1.grow_guide import (
    day,
    feed,
    grow_guide,
    week,
)
from app.api.v1.user import (
    user,
    user_allotment,
    user_preference,
)

router = APIRouter()

router.include_router(health.router, prefix="/health", tags=["Health"])
router.include_router(
    registration.router, prefix="/registration", tags=["Registration"]
)
router.include_router(user.router, prefix="/users", tags=["User"])
router.include_router(auth.router, prefix="/auth", tags=["Auth"])
router.include_router(
    user_allotment.router, prefix="/users/allotment", tags=["User Allotment"]
)
router.include_router(
    user_preference.router, prefix="/users/preferences", tags=["User Preferences"]
)
router.include_router(family.router, prefix="/families", tags=["Families"])
router.include_router(feed.router, prefix="/feed", tags=["Feed"])
router.include_router(day.router, prefix="/days", tags=["Days"])
router.include_router(week.router, prefix="/weeks", tags=["Weeks"])
router.include_router(grow_guide.router, prefix="/grow-guide", tags=["Grow Guide"])
