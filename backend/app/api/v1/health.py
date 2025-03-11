"""
Health Endpoint
"""

import time
import psutil
from fastapi import APIRouter
from app.api.core.config import settings

router = APIRouter()

START_TIME: float = time.time()

@router.get("/", tags=["Health"])
def health_check(
):
    """Health check endpoint"""

    uptime_seconds: float = round(time.time() - START_TIME, 2)
    cpu_usage: float = psutil.cpu_percent()
    memory_usage: float = psutil.virtual_memory().percent
    disk_usage: float = psutil.disk_usage("/").percent

    return {
        "status": "OK",
        "uptime": uptime_seconds,
        "version": settings.APP_VERSION,
        "resources": {
            "cpu_usage": f"{cpu_usage}%",
            "memory_usage": f"{memory_usage}%",
            "disk_usage": f"{disk_usage}%",
        },
    }
