"""
Application Settings
"""

import os
from pathlib import Path
from typing import Any, List, Optional, Type

import structlog
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource

from app.api.middleware.logging_middleware import sanitize_error_message

logger = structlog.get_logger()

BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent


def get_env_file() -> Optional[str]:
    """Get the appropriate .env file based on availability."""
    env_file = BASE_DIR / "app" / ".env"
    env_template = BASE_DIR / "app" / ".env.template"

    if env_file.exists():
        return str(env_file)
    elif env_template.exists():
        logger.warning("Using .env.template as fallback")
        return str(env_template)
    return None


class CustomDotEnvSettingsSource(DotEnvSettingsSource):
    """Custom DotEnv settings source that handles comma-separated string lists."""

    def decode_complex_value(self, field_name: str, field: Any, value: str) -> Any:
        """Override the complex value decoder to handle comma-separated lists for CORS settings."""
        if field_name in [
            "CORS_ORIGINS",
            "CORS_ALLOW_METHODS",
            "CORS_ALLOW_HEADERS",
        ] and isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            logger.debug(f"Parsed comma-separated {field_name}", items=items)
            return items

        try:
            return super().decode_complex_value(field_name, field, value)
        except ValueError as e:
            if field_name in [
                "CORS_ORIGINS",
                "CORS_ALLOW_METHODS",
                "CORS_ALLOW_HEADERS",
            ] and isinstance(value, str):
                items = [item.strip() for item in value.split(",") if item.strip()]
                logger.debug(f"Fallback parsing for {field_name}", items=items)
                return items
            raise e


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
    JWT_PRIVATE_KEY: str
    JWT_PUBLIC_KEY: str
    PRIVATE_KEY: bytes = b""
    PUBLIC_KEY: bytes = b""

    model_config = SettingsConfigDict(
        env_file=get_env_file(),
        env_file_encoding="utf-8",
    )

    @classmethod
    def settings_customise_sources(
        cls,
        settings_cls: Type[BaseSettings],
        init_settings: Any,
        env_settings: Any,
        dotenv_settings: Any,
        file_secret_settings: Any,
    ) -> tuple[Any, ...]:
        """Customize settings source."""
        # In production, prioritize system environment variables
        if os.environ.get("ENVIRONMENT") == "production":
            return init_settings, env_settings, file_secret_settings

        # In development, use the custom dotenv source
        return (
            init_settings,
            env_settings,
            CustomDotEnvSettingsSource(
                settings_cls=settings_cls,
                env_file=get_env_file(),
                env_file_encoding="utf-8",
            ),
            file_secret_settings,
        )

    @field_validator(
        "CORS_ORIGINS", "CORS_ALLOW_METHODS", "CORS_ALLOW_HEADERS", mode="before"
    )
    @classmethod
    def split_comma_separated_values(cls, value: Any) -> List[str]:
        """Parse comma-separated strings into lists for CORS settings."""
        if isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            logger.debug("Parsed comma-separated string into list", items=items)
            return items
        return value if isinstance(value, list) else []

    @model_validator(mode="after")
    def set_jwt_keys(self) -> "Settings":
        """Process JWT keys after model initialization."""
        try:
            private_key = self.JWT_PRIVATE_KEY.replace("\\n", "\n")
            public_key = self.JWT_PUBLIC_KEY.replace("\\n", "\n")

            self.PRIVATE_KEY = private_key.encode("utf-8")
            self.PUBLIC_KEY = public_key.encode("utf-8")
            logger.info("JWT keys loaded successfully from environment variables")
        except Exception as e:
            logger.error(
                "Failed to load JWT keys from environment variables",
                error=sanitize_error_message(str(e)),
                environment=self.ENVIRONMENT,
            )
            raise ValueError("Invalid JWT key format in environment variables") from e
        return self

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        logger.info(
            "Initializing application configuration",
            app_name=self.APP_NAME,
            version=self.APP_VERSION,
            environment=self.ENVIRONMENT,
        )


try:
    settings = Settings()
    logger.info(
        "Settings initialized successfully",
        app_name=settings.APP_NAME,
        version=settings.APP_VERSION,
        api_prefix=settings.API_PREFIX,
        environment=settings.ENVIRONMENT,
    )
except Exception as e:
    logger.error(
        "Settings initialization failed",
        error=sanitize_error_message(str(e))
        if "sanitize_error_message" in globals()
        else str(e),
        error_type=type(e).__name__,
    )
    raise
