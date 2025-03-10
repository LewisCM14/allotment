"""
Application Entrypoint
"""

from fastapi import FastAPI

from app.api.v1 import router as api_router

app = FastAPI(title="Allotment_service", version="0.0.0")

app.include_router(api_router, prefix="/api/v1")


@app.get("/")
def root():
    """Application Root"""
    return {"message": "Welcome to the Allotment Service API!"}
