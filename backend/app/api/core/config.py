"""
Application Settings
"""

import os
from pathlib import Path
from typing import Any, Dict

import yaml
from pydantic_settings import BaseSettings

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str
    APP_VERSION: str
    DATABASE_URL: str
    LOG_FILE: str

    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PRIVATE_KEY_PATH: str
    PUBLIC_KEY_PATH: str
    PRIVATE_KEY: bytes | None = None
    PUBLIC_KEY: bytes | None = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

        self.PRIVATE_KEY_PATH = str(BASE_DIR / self.PRIVATE_KEY_PATH)
        self.PUBLIC_KEY_PATH = str(BASE_DIR / self.PUBLIC_KEY_PATH)

        self.PRIVATE_KEY = self._load_key(self.PRIVATE_KEY_PATH)
        self.PUBLIC_KEY = self._load_key(self.PUBLIC_KEY_PATH)

    def _load_key(self, path: str) -> bytes:
        """Reads RSA key files safely."""
        if path and os.path.exists(path):
            with open(path, "rb") as key_file:
                return key_file.read()
        raise FileNotFoundError(
            f"Key file {path} not found. Ensure correct path in settings.yml"
        )


def load_yaml_config() -> Dict[str, Any]:
    """Loads YAML configuration from settings.yml.

    Returns:
        Dict[str, Any]: Configuration dictionary from YAML or empty dict if file not found
    """
    config_path = "app/settings.yml"
    if os.path.exists(config_path):
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if not isinstance(config, dict):
                return {}
            return config
    return {}


yaml_config = load_yaml_config()


settings = Settings(
    APP_NAME=yaml_config.get("app", {}).get("name", "Allotment Service"),
    APP_VERSION=yaml_config.get("app", {}).get("version", "0.0.0"),
    LOG_FILE=yaml_config.get("app", {}).get("log_file", "app.log"),
    DATABASE_URL=yaml_config.get("database", {}).get("url"),
    JWT_ALGORITHM=yaml_config.get("jwt", {}).get("algorithm", "RS256"),
    ACCESS_TOKEN_EXPIRE_MINUTES=yaml_config.get("jwt", {}).get(
        "access_token_expire_minutes", 60
    ),
    PRIVATE_KEY_PATH=yaml_config.get("jwt", {}).get("private_key_path", "private.pem"),
    PUBLIC_KEY_PATH=yaml_config.get("jwt", {}).get("public_key_path", "public.pem"),
)
