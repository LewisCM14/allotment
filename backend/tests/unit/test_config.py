from app.api.core import config


def test_settings_env(monkeypatch):
    monkeypatch.setenv("TEST_ENV_VAR", "test_value")
    assert config.os.getenv("TEST_ENV_VAR") == "test_value"


def test_settings_reload(monkeypatch):
    monkeypatch.setenv("RELOAD", "1")
    assert config.os.getenv("RELOAD") == "1"
