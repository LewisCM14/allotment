"""
Application Settings
"""

import os
from pathlib import Path
from typing import Any, Dict, List

import structlog
import yaml
from pydantic import SecretStr
from pydantic_settings import BaseSettings

logger = structlog.get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str
    APP_VERSION: str
    API_PREFIX: str

    DATABASE_URL: str
    FRONTEND_URL: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr

    LOG_LEVEL: str
    LOG_TO_FILE: bool
    LOG_FILE: str

    ENVIRONMENT: str
    SLOW_QUERY_THRESHOLD: float

    CORS_ORIGINS: List[str]
    CORS_ALLOW_CREDENTIALS: bool
    CORS_ALLOW_METHODS: List[str]
    CORS_ALLOW_HEADERS: List[str]

    JWT_ALGORITHM: str
    ACCESS_TOKEN_EXPIRE_MINUTES: int
    REFRESH_TOKEN_EXPIRE_DAYS: int
    RESET_TOKEN_EXPIRE_MINUTES: int
    PRIVATE_KEY_PATH: str
    PUBLIC_KEY_PATH: str
    REQUIRE_KEYS: bool = True  # Default to requiring keys
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
            # Only require keys if REQUIRE_KEYS is True
            self.PRIVATE_KEY = self._load_key(self.PRIVATE_KEY_PATH, required=self.REQUIRE_KEYS)
            self.PUBLIC_KEY = self._load_key(self.PUBLIC_KEY_PATH, required=self.REQUIRE_KEYS)
            if self.PRIVATE_KEY and self.PUBLIC_KEY:
                logger.info(
                    "Key files loaded successfully",
                    private_key_path=self.PRIVATE_KEY_PATH,
                    public_key_path=self.PUBLIC_KEY_PATH,
                )
            elif not self.REQUIRE_KEYS:
                logger.warning(
                    "Key validation skipped, using dummy keys",
                    environment=self.ENVIRONMENT,
                )
                # Generate dummy keys for testing environments
                if not self.PRIVATE_KEY:
                    self.PRIVATE_KEY = b"DUMMY_PRIVATE_KEY"
                if not self.PUBLIC_KEY:
                    self.PUBLIC_KEY = b"DUMMY_PUBLIC_KEY"
        except FileNotFoundError:
            if self.REQUIRE_KEYS:
                logger.error("Failed to load key files", error="REDACTED")
                raise
            else:
                logger.warning("Key files not found, but not required in this environment")
                self.PRIVATE_KEY = b"DUMMY_PRIVATE_KEY"
                self.PUBLIC_KEY = b"DUMMY_PUBLIC_KEY"

    def _load_key(self, path: str, required: bool = True) -> bytes | None:
        """Reads RSA key files safely."""
        if path and os.path.exists(path):
            try:
                with open(path, "rb") as key_file:
                    logger.debug("Loading key file", path=path)
                    return key_file.read()
            except IOError:
                logger.error("Error reading key file", path=path, error="REDACTED")
                if required:
                    raise
                return None
        if required:
            error_msg = (
                f"Key file {path} not found. Ensure correct path in settings.yml"
            )
            logger.error("Key file not found", path=path)
            raise FileNotFoundError(error_msg)
        logger.warning("Key file not found, skipping", path=path)
        return None


def load_yaml_config() -> Dict[str, Any]:
    """Loads YAML configuration from settings.yml.

    Returns:
        Dict[str, Any]: Configuration dictionary from YAML or empty dict if file not found
    """
    config_path = "app/settings.yml"
    template_path = "app/settings.template.yml"
    logger.info("Loading configuration", path=config_path)

    if not os.path.exists(config_path):
        logger.warning(
            "Configuration file not found, falling back to template", path=config_path
        )
        if os.path.exists(template_path):
            config_path = template_path
            logger.info("Loading configuration from template", path=template_path)
        else:
            return {}

    try:
        with open(config_path, "r", encoding="utf-8") as file:
            config = yaml.safe_load(file)
            if not isinstance(config, dict):
                logger.warning("Invalid YAML configuration format", path=config_path)
                return {}
            logger.info("Configuration loaded successfully")
            return config
    except (yaml.YAMLError, IOError):
        logger.error("Error loading configuration", path=config_path, error="REDACTED")
        return {}


yaml_config = load_yaml_config()

try:
    settings = Settings(
        APP_NAME=yaml_config.get("app", {}).get("name", "Allotment Service"),
        APP_VERSION=yaml_config.get("app", {}).get("version", "0.0.0"),
        API_PREFIX=yaml_config.get("app", {}).get("api_prefix", "/api/v1"),
        DATABASE_URL=yaml_config.get("database", {}).get("url"),
        FRONTEND_URL=yaml_config.get("frontend", {}).get("url"),
        MAIL_USERNAME=yaml_config.get("mail", {}).get("username"),
        MAIL_PASSWORD=SecretStr(yaml_config.get("mail", {}).get("password")),
        LOG_LEVEL=yaml_config.get("app", {}).get("log_level", "INFO"),
        LOG_TO_FILE=yaml_config.get("app", {}).get("log_to_file", True),
        LOG_FILE=yaml_config.get("app", {}).get("log_file", "app.log"),
        ENVIRONMENT=yaml_config.get("app", {}).get("environment", "development"),
        SLOW_QUERY_THRESHOLD=yaml_config.get("app", {}).get(
            "slow_query_threshold", 1.0
        ),
        CORS_ORIGINS=yaml_config.get("app", {}).get("cors", {}).get("origins"),
        CORS_ALLOW_CREDENTIALS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_credentials"),
        CORS_ALLOW_METHODS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_methods"),
        CORS_ALLOW_HEADERS=yaml_config.get("app", {})
        .get("cors", {})
        .get("allow_headers"),
        JWT_ALGORITHM=yaml_config.get("jwt", {}).get("algorithm"),
        ACCESS_TOKEN_EXPIRE_MINUTES=yaml_config.get("jwt", {}).get(
            "access_token_expire_minutes"
        ),
        REFRESH_TOKEN_EXPIRE_DAYS=yaml_config.get("jwt", {}).get(
            "refresh_token_expire_days"
        ),
        RESET_TOKEN_EXPIRE_MINUTES=yaml_config.get("jwt", {}).get(
            "reset_token_expire_minutes"
        ),
        PRIVATE_KEY_PATH=yaml_config.get("jwt", {}).get(
            "private_key_path", "app/keys/private.pem"
        ),
        PUBLIC_KEY_PATH=yaml_config.get("jwt", {}).get(
            "public_key_path", "app/keys/public.pem"
        ),
        REQUIRE_KEYS=yaml_config.get("jwt", {}).get("require_keys", True),
    )
    logger.info(
        "Settings initialized successfully",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_prefix=settings.API_PREFIX,
    )
except Exception as e:
    logger.error(
        "Settings initialization failed", error="REDACTED", error_type=type(e).__name__
    )
    raise
