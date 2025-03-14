"""
Application Settings
"""

import os

import yaml
from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str
    APP_VERSION: str
    DATABASE_URL: str


def load_yaml_config():
    """Loads YAML configuration from settings.yml."""
    config_path = "app/settings.yml"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            return yaml.safe_load(file)
    return {}


yaml_config = load_yaml_config()


settings = Settings(
    APP_NAME=yaml_config.get("app", {}).get("name", "Allotment Service"),
    APP_VERSION=yaml_config.get("app", {}).get("version", "0.0.0"),
    DATABASE_URL=yaml_config.get("database", {}).get("url"),
)
