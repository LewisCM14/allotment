import os

import pytest

from app.api.core.config import Settings


# Helper to patch environment variables
def set_env_vars(env_vars):
    for key, value in env_vars.items():
        os.environ[key] = value


def clear_env_vars(keys):
    for key in keys:
        if key in os.environ:
            del os.environ[key]


def minimal_env():
    return {
        "APP_NAME": "TestApp",
        "APP_VERSION": "0.1.0",
        "API_PREFIX": "/api",
        "DATABASE_URL": "sqlite:///:memory:",
        "FRONTEND_URL": "http://localhost:3000",
        "MAIL_USERNAME": "user@example.com",
        "MAIL_PASSWORD": "secret",
        "LOG_LEVEL": "INFO",
        "LOG_TO_FILE": "false",
        "LOG_FILE": "app.log",
        "ENVIRONMENT": "test",
        "SLOW_QUERY_THRESHOLD": "0.5",
        "CORS_ORIGINS": "http://localhost,http://127.0.0.1",
        "CORS_ALLOW_CREDENTIALS": "true",
        "CORS_ALLOW_METHODS": "GET,POST",
        "CORS_ALLOW_HEADERS": "Authorization,Content-Type",
        "JWT_ALGORITHM": "RS256",
        "ACCESS_TOKEN_EXPIRE_MINUTES": "15",
        "REFRESH_TOKEN_EXPIRE_DAYS": "7",
        "RESET_TOKEN_EXPIRE_MINUTES": "30",
        "JWT_PRIVATE_KEY": "-----BEGIN PRIVATE KEY-----\\nabc\\n-----END PRIVATE KEY-----",
        "JWT_PUBLIC_KEY": "-----BEGIN PUBLIC KEY-----\\ndef\\n-----END PUBLIC KEY-----",
    }


class TestSettingsConfig:
    @pytest.fixture
    def patch_env(self, monkeypatch):
        env = minimal_env()
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        yield env
        for k in env:
            monkeypatch.delenv(k, raising=False)

    def test_cors_settings_are_parsed(self, patch_env):
        settings = Settings()
        assert settings.CORS_ORIGINS == ["http://localhost", "http://127.0.0.1"]
        assert settings.CORS_ALLOW_METHODS == ["GET", "POST"]
        assert settings.CORS_ALLOW_HEADERS == ["Authorization", "Content-Type"]

    def test_jwt_keys_are_processed(self, patch_env):
        settings = Settings()
        assert b"BEGIN PRIVATE KEY" in settings.PRIVATE_KEY
        assert b"abc" in settings.PRIVATE_KEY
        assert b"BEGIN PUBLIC KEY" in settings.PUBLIC_KEY
        assert b"def" in settings.PUBLIC_KEY
        # Should contain real newlines
        assert b"\n" in settings.PRIVATE_KEY
        assert b"\n" in settings.PUBLIC_KEY

    def test_invalid_jwt_key_raises(self, monkeypatch):
        env = minimal_env()
        env["JWT_PRIVATE_KEY"] = ""
        env["JWT_PUBLIC_KEY"] = ""
        for k, v in env.items():
            monkeypatch.setenv(k, v)
        with pytest.raises(ValueError):
            Settings()
