"""
Application Settings
"""

import os
from pathlib import Path
from typing import Any, Dict, List

import structlog
import yaml
from pydantic_settings import BaseSettings

logger = structlog.get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str
    APP_VERSION: str
    API_PREFIX: str

    DATABASE_URL: str

    LOG_TO_FILE: bool
    LOG_FILE: str

    CORS_ORIGINS: List[str]
    CORS_ALLOW_CREDENTIALS: bool
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]

    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    PRIVATE_KEY_PATH: str
    PUBLIC_KEY_PATH: str
    PRIVATE_KEY: bytes | None = None
    PUBLIC_KEY: bytes | None = None

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        logger.info(
            "Initializing application configuration",
            app_name=self.APP_NAME,
            version=self.APP_VERSION,
        )

        self.PRIVATE_KEY_PATH = str(BASE_DIR / self.PRIVATE_KEY_PATH)
        self.PUBLIC_KEY_PATH = str(BASE_DIR / self.PUBLIC_KEY_PATH)

        try:
            self.PRIVATE_KEY = self._load_key(self.PRIVATE_KEY_PATH)
            self.PUBLIC_KEY = self._load_key(self.PUBLIC_KEY_PATH)
            logger.info(
                "Key files loaded successfully",
                private_key_path=self.PRIVATE_KEY_PATH,
                public_key_path=self.PUBLIC_KEY_PATH,
            )
        except FileNotFoundError as e:
            logger.error("Failed to load key files", error=str(e))
            raise

    def _load_key(self, path: str) -> bytes:
        """Reads RSA key files safely."""
        if path and os.path.exists(path):
            try:
                with open(path, "rb") as key_file:
                    logger.debug("Loading key file", path=path)
                    return key_file.read()
            except IOError as e:
                logger.error("Error reading key file", path=path, error=str(e))
                raise
        error_msg = f"Key file {path} not found. Ensure correct path in settings.yml"
        logger.error("Key file not found", path=path)
        raise FileNotFoundError(error_msg)


def load_yaml_config() -> Dict[str, Any]:
    """Loads YAML configuration from settings.yml.

    Returns:
        Dict[str, Any]: Configuration dictionary from YAML or empty dict if file not found
    """
    config_path = "app/settings.yml"
    logger.info("Loading configuration", path=config_path)

    if not os.path.exists(config_path):
        logger.warning("Configuration file not found", path=config_path)
        return {}

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if not isinstance(config, dict):
                logger.warning("Invalid YAML configuration format", path=config_path)
                return {}
            logger.info("Configuration loaded successfully")
            return config
    except (yaml.YAMLError, IOError) as e:
        logger.error("Error loading configuration", path=config_path, error=str(e))
        return {}


yaml_config = load_yaml_config()

try:
    settings = Settings(
        APP_NAME=yaml_config.get("app", {}).get("name", "Allotment Service"),
        APP_VERSION=yaml_config.get("app", {}).get("version", "0.0.0"),
        API_PREFIX=yaml_config.get("app", {}).get("api_prefix", "/api/v1"),
        DATABASE_URL=yaml_config.get("database", {}).get("url"),
        LOG_TO_FILE=yaml_config.get("app", {}).get("log_to_file", True),
        LOG_FILE=yaml_config.get("app", {}).get("log_file", "app.log"),
        CORS_ORIGINS=yaml_config.get("app", {})
        .get("cors", {})
        .get("origins", ["http://127.0.0.1:5173"]),
        CORS_ALLOW_CREDENTIALS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_credentials", True),
        CORS_ALLOW_METHODS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_methods", ["*"]),
        CORS_ALLOW_HEADERS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_headers", ["*"]),
        JWT_ALGORITHM=yaml_config.get("jwt", {}).get("algorithm", "RS256"),
        ACCESS_TOKEN_EXPIRE_MINUTES=yaml_config.get("jwt", {}).get(
            "access_token_expire_minutes", 60
        ),
        PRIVATE_KEY_PATH=yaml_config.get("jwt", {}).get(
            "private_key_path", "private.pem"
        ),
        PUBLIC_KEY_PATH=yaml_config.get("jwt", {}).get("public_key_path", "public.pem"),
    )
    logger.info(
        "Settings initialized successfully",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_prefix=settings.API_PREFIX,
    )
except Exception as e:
    logger.error(
        "Settings initialization failed", error=str(e), error_type=type(e).__name__
    )
    raise
