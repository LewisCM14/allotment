"""
Application Settings
"""
import os

class Settings:
    """Application configuration settings."""

    APP_NAME: str = "Allotment Service"
    APP_VERSION = os.getenv("APP_VERSION", "0.0.0")

settings = Settings()
