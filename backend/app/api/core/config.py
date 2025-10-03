"""
Application Settings
"""

import os
from pathlib import Path
from typing import Any, List, Optional, Type

import structlog
from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic_settings.sources import DotEnvSettingsSource, EnvSettingsSource

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


class CustomEnvSettingsSource(EnvSettingsSource):
    """Custom environment settings source that handles comma-separated string lists."""

    def prepare_field_value(
        self, field_name: str, field: Any, value: Any, value_is_complex: bool
    ) -> Any:
        """Handle comma-separated values for list-type fields in environment variables."""
        if field_name in [
            "CORS_ORIGINS",
            "CORS_ALLOW_METHODS",
            "CORS_ALLOW_HEADERS",
        ] and isinstance(value, str):
            items = [item.strip() for item in value.split(",") if item.strip()]
            logger.debug(f"Parsed comma-separated {field_name} from env", items=items)
            return items

        return super().prepare_field_value(field_name, field, value, value_is_complex)


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
            logger.debug(f"Parsed comma-separated {field_name} from .env", items=items)
            return items

        return super().decode_complex_value(field_name, field, value)


class Settings(BaseSettings):
    """Application configuration settings."""

    APP_NAME: str
    APP_VERSION: str
    API_PREFIX: str

    DATABASE_URL: str
    FRONTEND_URL: str

    MAIL_USERNAME: str
    MAIL_PASSWORD: SecretStr
    MAIL_PORT: int
    MAIL_SSL_TLS: bool
    MAIL_STARTTLS: bool

    LOG_LEVEL: str
    LOG_TO_FILE: bool
    LOG_FILE: str
    LOG_MAX_BYTES: int
    LOG_BACKUP_COUNT: int

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
        """Customize settings source to properly handle environment variables."""
        custom_env_settings = CustomEnvSettingsSource(
            settings_cls=settings_cls,
        )

        if os.getenv("ENVIRONMENT") == "production":
            logger.info("Using production settings configuration")
            return custom_env_settings, init_settings, file_secret_settings
        else:
            logger.info(
                f"Using {os.getenv('ENVIRONMENT', 'development')} settings configuration"
            )
            return (
                init_settings,
                custom_env_settings,
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
            jwt_private_key_str = str(self.JWT_PRIVATE_KEY).strip()
            jwt_public_key_str = str(self.JWT_PUBLIC_KEY).strip()

            if not jwt_private_key_str or not jwt_public_key_str:
                logger.error(
                    "JWT keys must not be empty",
                    environment=self.ENVIRONMENT,
                )
                raise ValueError("JWT keys must not be empty")

            def process_key_string(key_str: str) -> str:
                # Define a unique placeholder that won't clash with Base64 characters or be affected by backslash replacement.
                placeholder = "___PLACEHOLDER_FOR_ACTUAL_NEWLINE___"
                # Step 1: Replace legitimate "\\n" sequences with the placeholder.
                processed_str = key_str.replace("\\n", placeholder)
                # Step 2: Replace any remaining single backslashes "\" with an actual newline "\n".
                # This handles cases like "\M" becoming "\nM".
                processed_str = processed_str.replace("\\", "\n")
                # Step 3: Replace the placeholder back with actual newlines "\n".
                processed_str = processed_str.replace(placeholder, "\n")
                return processed_str

            private_key = process_key_string(jwt_private_key_str)
            public_key = process_key_string(jwt_public_key_str)

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
        try:
            super().__init__(**kwargs)
            logger.info(
                "Initializing application configuration",
                app_name=self.APP_NAME,
                version=self.APP_VERSION,
                environment=self.ENVIRONMENT,
            )
        except Exception as e:
            logger.error(
                "Failed to initialize settings",
                error=sanitize_error_message(str(e)),
                error_type=type(e).__name__,
            )
            raise


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
