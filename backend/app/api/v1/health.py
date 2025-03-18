"""
Health Endpoints
"""

import time

import psutil
from fastapi import APIRouter, Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.config import settings
from app.api.core.database import get_db

router = APIRouter()
START_TIME = time.time()

@router.get("/", tags=["Health"])
async def health_check(
    db: AsyncSession = Depends(get_db),
):
    """Health check endpoint"""
    
    uptime_seconds: float = round(time.time() - START_TIME, 2)
    
    try:
        result = await db.execute(text("SELECT 1"))
        await result.scalar()
        db_status = "healthy"
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"

    return {
        "status": "ok",
        "uptime": uptime_seconds,
        "version": settings.APP_VERSION,
        "database": db_status,
        "resources": {
            "cpu_usage": psutil.cpu_percent(),
            "memory_usage": psutil.virtual_memory().percent,
            "disk_usage": psutil.disk_usage("/").percent,
        },
    }
