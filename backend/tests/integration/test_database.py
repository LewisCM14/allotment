import pytest
from sqlalchemy import text

from app.api.core import database


class TestDatabaseIntegration:
    @pytest.mark.asyncio
    async def test_get_db_yields_session(self, monkeypatch):
        monkeypatch.setattr(database.logger, "debug", lambda *a, **k: None)
        monkeypatch.setattr(database.logger, "error", lambda *a, **k: None)
        monkeypatch.setattr(database.logger, "info", lambda *a, **k: None)
        agen = database.get_db()
        session = await agen.__anext__()
        assert session is not None
        try:
            await agen.__anext__()
        except StopAsyncIteration:
            pass

    @pytest.mark.asyncio
    async def test_db_event_handlers(self, monkeypatch):
        monkeypatch.setattr(database.logger, "debug", lambda *a, **k: None)
        monkeypatch.setattr(database.logger, "warning", lambda *a, **k: None)
        async with database.AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT 1"))
            assert result is not None
