from __future__ import annotations

from unittest.mock import AsyncMock

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.repositories.user.user_repository import UserRepository
from tests.test_helpers import (
    make_user_allotment,
    make_user_feed_day,
    make_user_model,
)


@pytest.fixture
def mock_db():
    """AsyncSession mock for repository tests."""
    return AsyncMock(spec=AsyncSession)


@pytest.fixture
def user_repository(mock_db):
    """UserRepository bound to mocked DB session."""
    return UserRepository(db=mock_db)


@pytest.fixture
def sample_user():
    return make_user_model(
        email="test@example.com",
        password_hash="hashed_password",
        first_name="Test",
        country_code="US",
    )


@pytest.fixture
def sample_allotment():
    return make_user_allotment(postal_code="12345", width=10.0, length=10.0)


@pytest.fixture
def sample_user_feed_day():
    return make_user_feed_day(feed_name="tomato feed", day_name="mon", day_number=1)
