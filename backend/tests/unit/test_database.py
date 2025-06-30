from app.api.core import database


def test_get_engine():
    engine = database.engine
    assert engine is not None


def test_get_session():
    session_maker = database.AsyncSessionLocal
    assert session_maker is not None
