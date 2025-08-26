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

from app.api.core.config import settings
from app.api.core.database import get_db
from app.api.core.limiter import limiter

logger = structlog.get_logger()

router = APIRouter()
START_TIME = time.time()

CPU_WARNING_THRESHOLD = 85
MEMORY_WARNING_THRESHOLD = 85
DISK_WARNING_THRESHOLD = 85

_previous_resources_state = {
    "cpu_critical": False,
    "memory_critical": False,
    "disk_critical": False,
    "any_critical": False,
}


@router.get(
    "",
    tags=["Health"],
    summary="Health check",
    description="Returns system health information",
)
@router.get("/", include_in_schema=False)
@limiter.limit("30/minute")
async def health_check(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> Dict[str, Union[str, float, Dict[str, float]]]:
    """Health check endpoint."""
    global _previous_resources_state
    uptime_seconds: float = round(time.time() - START_TIME, 2)

    try:
        result = await db.scalar(text("SELECT 1"))
        db_status = "healthy" if result == 1 else "unhealthy"
        logger.info("Database health check", status=db_status)
    except Exception as e:
        db_status = "unhealthy"
        logger.error(
            "Database health check failed",
            error="Database connectivity issue",
            error_type=type(e).__name__,
        )

    cpu_usage = psutil.cpu_percent()
    memory_usage = psutil.virtual_memory().percent
    disk_usage = psutil.disk_usage("/").percent

    logger.debug(
        "System resources status",
        cpu_usage=cpu_usage,
        memory_usage=memory_usage,
        disk_usage=disk_usage,
    )

    current_state = {
        "cpu_critical": cpu_usage > CPU_WARNING_THRESHOLD,
        "memory_critical": memory_usage > MEMORY_WARNING_THRESHOLD,
        "disk_critical": disk_usage > DISK_WARNING_THRESHOLD,
    }
    current_state["any_critical"] = any(
        [
            current_state["cpu_critical"],
            current_state["memory_critical"],
            current_state["disk_critical"],
        ]
    )

    if current_state["any_critical"] != _previous_resources_state["any_critical"]:
        if current_state["any_critical"]:
            logger.warning(
                "System resources near capacity",
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
            )
        else:
            logger.info(
                "System resources returned to normal levels",
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                disk_usage=disk_usage,
            )

    if (
        current_state["cpu_critical"] != _previous_resources_state["cpu_critical"]
        and current_state["cpu_critical"]
    ):
        logger.warning("CPU usage critical", cpu_usage=cpu_usage)

    if (
        current_state["memory_critical"] != _previous_resources_state["memory_critical"]
        and current_state["memory_critical"]
    ):
        logger.warning("Memory usage critical", memory_usage=memory_usage)

    if (
        current_state["disk_critical"] != _previous_resources_state["disk_critical"]
        and current_state["disk_critical"]
    ):
        logger.warning("Disk usage critical", disk_usage=disk_usage)

    _previous_resources_state = current_state

    response: Dict[str, Union[str, float, Dict[str, float]]] = {
        "status": "ok" if db_status == "healthy" else "degraded",
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
