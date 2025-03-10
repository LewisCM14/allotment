"""
Health Endpoint
"""

from fastapi import APIRouter

router = APIRouter()


@router.get("/", status_code=200, tags=["Health"])
def health_check():
    """Health Check Endpoint"""
    return {"status": "OK"}
