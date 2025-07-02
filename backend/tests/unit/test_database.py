
import pytest
from app.api.core import database
from sqlalchemy import text

def test_get_engine():
    engine = database.engine
    assert engine is not None


def test_get_session():
    session_maker = database.AsyncSessionLocal
    assert session_maker is not None



@pytest.mark.asyncio
async def test_get_db_yields_session(monkeypatch):
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
async def test_db_event_handlers(monkeypatch):
    monkeypatch.setattr(database.logger, "debug", lambda *a, **k: None)
    monkeypatch.setattr(database.logger, "warning", lambda *a, **k: None)
    async with database.AsyncSessionLocal() as session:
        result = await session.execute(text("SELECT 1"))
        assert result is not None
