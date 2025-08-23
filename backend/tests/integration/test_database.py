import pytest
from sqlalchemy import text

from app.api.core import database
from tests.conftest import TestingSessionLocal


@pytest.fixture
def silence_db_logger(monkeypatch, tmp_path):
    """Silence noisy database logger levels for deterministic assertions.

    Uses a temporary log file and patches application settings so tests do not
    create or modify `app/app.log` inside the repository.
    """
    for level in ["debug", "error", "info", "warning"]:
        monkeypatch.setattr(database.logger, level, lambda *a, **k: None)

    # Use a temporary file for logging and patch settings to point at it.
    temp_log_file = tmp_path / "app.log"
    temp_log_file.parent.mkdir(parents=True, exist_ok=True)

    # Patch the settings LOG_FILE to the temporary path to avoid repo writes
    from app.api.core.config import settings

    monkeypatch.setattr(settings, "LOG_FILE", str(temp_log_file))


@pytest.mark.asyncio
async def test_get_db_yields_single_session(silence_db_logger, monkeypatch):
    """get_db() yields one session then closes (StopAsyncIteration on second pull)."""
    # Patch the database module to use the test session factory (SQLite)
    monkeypatch.setattr(database, "AsyncSessionLocal", TestingSessionLocal)
    agen = database.get_db()
    session = await agen.__anext__()
    assert session is not None
    # Session should be usable
    result = await session.execute(text("SELECT 1"))
    assert result.scalar() == 1
    # Second pull should raise StopAsyncIteration (generator exhausted)
    with pytest.raises(StopAsyncIteration):
        await agen.__anext__()


@pytest.mark.asyncio
async def test_session_basic_query(silence_db_logger):
    """Basic sanity check using explicit TestingSessionLocal factory."""
    async with TestingSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result.scalar() == 1


@pytest.mark.asyncio
async def test_get_db_rollback_on_exception(monkeypatch):
    """Ensure rollback invoked & exception re-raised when inner block errors."""
    # Track whether rollback called via wrapper
    called = {"rollback": False, "close": False}

    # Wrap AsyncSessionLocal to produce a session whose rollback we can monitor
    real_factory = database.AsyncSessionLocal

    from contextlib import asynccontextmanager

    @asynccontextmanager
    async def _session_factory():
        async with real_factory() as sess:
            orig_rollback = sess.rollback
            orig_close = sess.close

            async def rollback_wrapper():
                called["rollback"] = True
                await orig_rollback()

            async def close_wrapper():
                called["close"] = True
                await orig_close()

            sess.rollback = rollback_wrapper
            sess.close = close_wrapper
            yield sess

    monkeypatch.setattr(database, "AsyncSessionLocal", _session_factory)
    monkeypatch.setattr(database.logger, "debug", lambda *a, **k: None)
    monkeypatch.setattr(database.logger, "error", lambda *a, **k: None)
    monkeypatch.setattr(database.logger, "info", lambda *a, **k: None)

    agen = database.get_db()
    session = await agen.__anext__()
    assert session is not None
    # Inject exception back into generator so get_db except path executes (rollback)
    with pytest.raises(RuntimeError):
        await agen.athrow(RuntimeError("boom"))
    # Both rollback and close should have been invoked
    assert called["rollback"] is True
    assert called["close"] is True
