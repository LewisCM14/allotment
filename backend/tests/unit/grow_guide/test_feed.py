"""
Unit tests for Feed API endpoints using real database fixtures
"""

from unittest.mock import Mock

import pytest
from fastapi import Request

from app.api.v1.feed import get_feeds
from tests.conftest import TestingSessionLocal


class TestFeedEndpointUnit:
    """Unit tests for feed endpoint functions."""

    @pytest.mark.asyncio
    async def test_get_feeds_unit_success(self, seed_feed_data):
        """Unit test for successful get_feeds function."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_feeds(mock_request, db)

            # Assert
            assert len(result) == 5  # We seeded 5 feeds

            # Verify we got feeds in the correct format
            feed_names = [feed.name for feed in result]
            assert "Tomato Feed" in feed_names
            assert "General Purpose Feed" in feed_names
            assert "Organic Compost" in feed_names

            # Verify each feed has an ID and name
            for feed in result:
                assert feed.id is not None
                assert feed.name is not None
                assert isinstance(feed.name, str)
                assert len(feed.name) > 0

    @pytest.mark.asyncio
    async def test_get_feeds_unit_empty_result(self):
        """Unit test for get_feeds with empty database."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act (no seed_feed_data fixture, so database is empty)
            result = await get_feeds(mock_request, db)

            # Assert
            assert len(result) == 0
            assert result == []

    @pytest.mark.asyncio
    async def test_get_feeds_unit_specific_data_validation(self, seed_feed_data):
        """Unit test to validate specific feed data."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_feeds(mock_request, db)

            # Assert
            assert len(result) == 5

            # Find specific feeds and validate their data
            tomato_feed = next(
                (feed for feed in result if feed.name == "Tomato Feed"), None
            )
            assert tomato_feed is not None
            assert tomato_feed.id is not None

            bone_meal = next(
                (feed for feed in result if feed.name == "Bone Meal"), None
            )
            assert bone_meal is not None
            assert bone_meal.id is not None

            # Verify all feeds have unique IDs
            ids = [feed.id for feed in result]
            assert len(ids) == len(set(ids))  # All IDs should be unique

            # Verify all feeds have unique names
            names = [feed.name for feed in result]
            assert len(names) == len(set(names))  # All names should be unique

    @pytest.mark.asyncio
    async def test_get_feeds_unit_data_types(self, seed_feed_data):
        """Unit test to validate feed data types."""
        # Arrange
        mock_request = Mock(spec=Request)

        async with TestingSessionLocal() as db:
            # Act
            result = await get_feeds(mock_request, db)

            # Assert
            assert len(result) == 5

            for feed in result:
                # Verify data types
                assert hasattr(feed, "id")
                assert hasattr(feed, "name")
                assert isinstance(feed.name, str)
                # ID should be UUID-like (string representation)
                assert feed.id is not None
