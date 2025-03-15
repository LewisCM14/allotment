"""
Health Endpoints
"""

import time

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import exc, text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.core.database import get_db

router = APIRouter()

START_TIME: float = time.time()


@router.get("/", tags=["Health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """Health check endpoint"""

    uptime_seconds: float = round(time.time() - START_TIME, 2)

    try:
        await db.execute(text("SELECT 1"))
        db_status = "healthy"
    except exc.SQLAlchemyError as e:
        db_status = f"unhealthy: {str(e)}"

    cpu_usage: float = psutil.cpu_percent()
    memory_usage: float = psutil.virtual_memory().percent
    disk_usage: float = psutil.disk_usage("/").percent

    return {
        "status": "OK",
        "uptime": uptime_seconds,
        "version": settings.APP_VERSION,
        "database": db_status,
        "resources": {
            "cpu_usage": f"{cpu_usage}%",
            "memory_usage": f"{memory_usage}%",
            "disk_usage": f"{disk_usage}%",
        },
    }
