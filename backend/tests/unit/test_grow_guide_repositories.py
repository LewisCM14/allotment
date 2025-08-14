"""
Test for Grow Guide Repositories
"""

from unittest.mock import Mock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository


@pytest.mark.asyncio
async def test_day_repository_get_all_days():
    """Test DayRepository get_all_days method."""
    # Arrange
    mock_db = Mock(spec=AsyncSession)
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    repo = DayRepository(mock_db)

    # Act
    result = await repo.get_all_days()

    # Assert
    assert result == []
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_variety_repository_get_all_feeds():
    """Test VarietyRepository get_all_feeds method."""
    # Arrange
    mock_db = Mock(spec=AsyncSession)
    mock_scalars = Mock()
    mock_scalars.all.return_value = []
    mock_result = Mock()
    mock_result.scalars.return_value = mock_scalars
    mock_db.execute.return_value = mock_result

    repo = VarietyRepository(mock_db)

    # Act
    result = await repo.get_all_feeds()

    # Assert
    assert result == []
    mock_db.execute.assert_called_once()
