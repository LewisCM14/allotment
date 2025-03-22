"""
Health Endpoints
- Provides system health information
- Monitors database connectivity
- Reports system resource usage
"""

import time
from typing import Dict, Union

import psutil
import structlog
from fastapi import APIRouter, Depends, Request
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.limiter import limiter
from app.api.core.config import settings
from app.api.core.database import get_db

logger = structlog.get_logger()

router = APIRouter()
START_TIME = time.time()


@router.get(
    "/",
    tags=["Health"],
    summary="Health check",
    description="Returns system health information",
)
@limiter.limit("10/minute")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Union[str, float, Dict[str, float]]]:
    """Health check endpoint."""
    uptime_seconds: float = round(time.time() - START_TIME, 2)

    logger.debug(
        "Health check initiated", uptime=uptime_seconds, version=settings.APP_VERSION
    )

    try:
        result = await db.scalar(text("SELECT 1"))
        db_status = "healthy" if result == 1 else "unhealthy"
        logger.info("Database health check", status=db_status, result=result)
    except Exception as e:
        db_status = f"unhealthy: {str(e)}"
        logger.error(
            "Database health check failed", error=str(e), error_type=type(e).__name__
        )

    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent

    logger.info(
        "System resources status",
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
    )

    if cpu_usage > 80 or memory_usage > 80 or disk_usage > 80:
        logger.warning(
            "System resources near capacity",
            cpu_usage=cpu_usage,
            memory_usage=memory_usage,
            disk_usage=disk_usage,
        )

    response: Dict[str, Union[str, float, Dict[str, float]]] = {
        "status": "ok",
        "uptime": uptime_seconds,
        "version": settings.APP_VERSION,
        "database": db_status,
        "resources": {
            "cpu_usage": cpu_usage,
            "memory_usage": memory_usage,
            "disk_usage": disk_usage,
        },
    }

    logger.debug("Health check completed", response=response)
    return response
