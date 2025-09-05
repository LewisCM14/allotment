"""
Test Variety Repository
"""

import pytest

from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from tests.conftest import TestingSessionLocal
from tests.test_helpers import make_variety


class TestVarietyRepository:
    @pytest.mark.asyncio
    async def test_get_all_feeds(self, seed_feed_data):
        """Test getting all feeds."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)
            feeds = await repo.get_all_feeds()

            assert len(feeds) == 5
            assert all(feed.feed_name for feed in feeds)

            # Check feeds are ordered by name
            names = [feed.feed_name for feed in feeds]
            assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_get_all_lifecycles(self, seed_lifecycle_data):
        """Test getting all lifecycles."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)
            lifecycles = await repo.get_all_lifecycles()

            assert len(lifecycles) == 3
            assert all(lifecycle.lifecycle_name for lifecycle in lifecycles)

            # Check lifecycles are ordered by name
            names = [lifecycle.lifecycle_name for lifecycle in lifecycles]
            assert names == sorted(names)

    @pytest.mark.asyncio
    async def test_get_all_planting_conditions(self, seed_planting_conditions_data):
        """Test getting all planting conditions."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)
            conditions = await repo.get_all_planting_conditions()

            assert len(conditions) == 4
            assert all(condition.planting_condition for condition in conditions)

    @pytest.mark.asyncio
    async def test_get_all_frequencies(self, seed_frequency_data):
        """Test getting all frequencies."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)
            frequencies = await repo.get_all_frequencies()

            assert len(frequencies) == 3
            assert all(freq.frequency_name for freq in frequencies)

    @pytest.mark.asyncio
    async def test_create_variety(self, authenticated_user):
        """Test creating a variety."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)

            variety = make_variety(
                owner_user_id=authenticated_user.user_id,
                variety_name="Test Repository Tomato",
            )

            created_variety = await repo.create_variety(variety)

            assert created_variety.variety_id is not None
            assert created_variety.variety_name == "Test Repository Tomato"
            assert created_variety.owner_user_id == authenticated_user.user_id

    @pytest.mark.asyncio
    async def test_variety_name_exists_for_user(
        self, user_in_database, seed_variety_data
    ):
        """Test checking if variety name exists for user."""
        import uuid

        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)

            user_id = uuid.UUID(user_in_database["user_id"])

            # Test with existing variety name
            exists = await repo.variety_name_exists_for_user(user_id, "Test Tomato")
            assert exists is True

            # Test with non-existing variety name
            exists = await repo.variety_name_exists_for_user(
                user_id, "Non-existing Variety"
            )
            assert exists is False

    @pytest.mark.asyncio
    async def test_get_user_varieties(self, user_in_database, seed_variety_data):
        """Test getting varieties for a user."""
        import uuid

        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)

            user_id = uuid.UUID(user_in_database["user_id"])
            varieties = await repo.get_user_varieties(user_id)

            assert len(varieties) >= 1
            assert all(v.owner_user_id == user_id for v in varieties)

    @pytest.mark.asyncio
    async def test_get_public_varieties(self, seed_public_variety_data):
        """Test getting public varieties."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)
            varieties = await repo.get_public_varieties()

            assert len(varieties) >= 1
            assert all(v.is_public for v in varieties)

    @pytest.mark.asyncio
    async def test_delete_variety(self, authenticated_user, seed_variety_data):
        """Test deleting a variety."""
        async with TestingSessionLocal() as db:
            repo = VarietyRepository(db)

            # Create a test variety using the helper function
            variety = make_variety(
                owner_user_id=authenticated_user.user_id,
                variety_name="Test Delete Variety",
            )

            created_variety = await repo.create_variety(variety)
            variety_id = created_variety.variety_id

            # Delete the variety
            success = await repo.delete_variety(variety_id, authenticated_user.user_id)
            assert success is True

            # Try to delete again (should fail)
            success = await repo.delete_variety(variety_id, authenticated_user.user_id)
            assert success is False
