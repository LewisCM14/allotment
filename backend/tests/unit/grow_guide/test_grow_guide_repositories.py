from unittest.mock import Mock

import pytest
from sqlalchemy.exc import IntegrityError, SQLAlchemyError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    DatabaseIntegrityError,
)
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository


def _mock_result(return_list):  # helper
    mock_scalars = Mock()
    mock_scalars.all.return_value = return_list
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars
    return mock_result


@pytest.mark.asyncio
async def test_day_repository_get_all_days_empty():
    mock_db = Mock(spec=AsyncSession)
    mock_db.execute.return_value = _mock_result([])
    repo = DayRepository(mock_db)
    result = await repo.get_all_days()
    assert result == []
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_day_repository_get_all_days_success_and_ordering():
    mock_db = Mock(spec=AsyncSession)
    # Intentionally unsorted input (repository query applies ordering)
    days = [
        Day(day_id=1, day_number=5, day_name="Fri"),
        Day(day_id=2, day_number=1, day_name="Mon"),
        Day(day_id=3, day_number=3, day_name="Wed"),
    ]
    mock_db.execute.return_value = _mock_result(days)
    repo = DayRepository(mock_db)
    result = await repo.get_all_days()
    # Since we mock execute, ordering isn't actually applied; assert passthrough
    assert result == days
    # Verify select statement had ordering clause
    statement = mock_db.execute.call_args[0][0]
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled and "day_number" in compiled


@pytest.mark.asyncio
async def test_variety_repository_get_all_feeds_empty():
    mock_db = Mock(spec=AsyncSession)
    mock_db.execute.return_value = _mock_result([])
    repo = VarietyRepository(mock_db)
    result = await repo.get_all_feeds()
    assert result == []
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_variety_repository_get_all_feeds_success_and_ordering():
    mock_db = Mock(spec=AsyncSession)
    feeds = [
        Feed(feed_id=1, feed_name="Zinc Mix"),
        Feed(feed_id=2, feed_name="All Purpose"),
        Feed(feed_id=3, feed_name="Bone Meal"),
    ]
    mock_db.execute.return_value = _mock_result(feeds)
    repo = VarietyRepository(mock_db)
    result = await repo.get_all_feeds()
    assert result == feeds
    statement = mock_db.execute.call_args[0][0]
    compiled = str(statement.compile(compile_kwargs={"literal_binds": True}))
    assert "ORDER BY" in compiled and "name" in compiled


@pytest.mark.asyncio
async def test_day_repository_integrity_error_translation():
    mock_db = Mock(spec=AsyncSession)
    # Simulate IntegrityError (non-unique specific -> generic translation)
    mock_db.execute.side_effect = IntegrityError(
        statement="SELECT * FROM day", params={}, orig=Exception("constraint fail")
    )
    repo = DayRepository(mock_db)
    with pytest.raises(DatabaseIntegrityError):
        await repo.get_all_days()


@pytest.mark.asyncio
async def test_variety_repository_sqlalchemy_error_translation():
    mock_db = Mock(spec=AsyncSession)
    mock_db.execute.side_effect = SQLAlchemyError("db boom")
    repo = VarietyRepository(mock_db)
    with pytest.raises(BusinessLogicError):
        await repo.get_all_feeds()
