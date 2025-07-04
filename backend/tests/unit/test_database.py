from app.api.core import database


class TestDatabaseCore:
    def test_get_engine(self):
        engine = database.engine
        assert engine is not None

    def test_get_session(self):
        session_maker = database.AsyncSessionLocal
        assert session_maker is not None
