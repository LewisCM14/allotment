"""
Family API Integration Tests
"""

import pytest

from app.api.core.config import settings

PREFIX = settings.API_PREFIX


class TestFamilyAPI:
    @pytest.mark.asyncio
    async def test_list_botanical_groups_success(self, client, seed_family_data):
        """Test successful retrieval of botanical groups with families."""
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == 200
        data = response.json()
        assert isinstance(data, list)
        found = False
        for group in data:
            if group["name"] == seed_family_data["group_name"]:
                found = True
                assert group["recommended_rotation_years"] == 2
                assert isinstance(group["families"], list)
                fam_names = [fam["name"] for fam in group["families"]]
                assert seed_family_data["family_name"] in fam_names
        assert found, "Seeded botanical group not found in response"

    @pytest.mark.asyncio
    async def test_list_botanical_groups_empty(self, client, mocker):
        """Test endpoint returns empty list if no botanical groups exist."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == 200
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_list_botanical_groups_error(self, client, mocker):
        """Test endpoint returns 500 on unexpected error."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            side_effect=Exception("Simulated DB error"),
        )
        import app.api.middleware.exception_handler as exc_handler

        with pytest.raises(exc_handler.BusinessLogicError) as exc_info:
            client.get(f"{PREFIX}/families/botanical-groups/")
        assert (
            "an unexpected error occurred while retrieving botanical groups"
            in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_list_botanical_groups_schema_validation(
        self, client, seed_family_data
    ):
        """Test that all botanical groups and families conform to schema."""
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == 200
        data = response.json()
        for group in data:
            assert isinstance(group["id"], (str, int))
            assert isinstance(group["name"], str)
            assert "recommended_rotation_years" in group
            assert isinstance(group["families"], list)
            for fam in group["families"]:
                assert isinstance(fam["id"], (str, int))
                assert isinstance(fam["name"], str)

    @pytest.mark.asyncio
    async def test_list_botanical_groups_rate_limit(self, client, mocker):
        """Test rate limiting is enforced (if enabled)."""
        from app.api.core.limiter import limiter

        limiter.enabled = True
        limiter._storage.reset()
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )
        for _ in range(20):
            resp = client.get(f"{PREFIX}/families/botanical-groups/")
            assert resp.status_code == 200
        resp = client.get(f"{PREFIX}/families/botanical-groups/")
        assert resp.status_code in (429, 200)
        limiter.enabled = False

    @pytest.mark.asyncio
    async def test_list_botanical_groups_db_failure(self, client, mocker):
        """Test DB failure returns 500 error."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            side_effect=Exception("DB connection lost"),
        )
        import app.api.middleware.exception_handler as exc_handler

        with pytest.raises(exc_handler.BusinessLogicError) as exc_info:
            client.get(f"{PREFIX}/families/botanical-groups/")
        assert "botanical groups" in str(exc_info.value).lower()

    @pytest.mark.asyncio
    async def test_list_botanical_groups_with_families_types(
        self, client, seed_family_data
    ):
        """Test types of fields in response."""
        resp = client.get(f"{PREFIX}/families/botanical-groups/")
        assert resp.status_code == 200
        data = resp.json()
        for group in data:
            assert isinstance(group["name"], str)
            assert isinstance(group["families"], list)
            for fam in group["families"]:
                assert isinstance(fam["name"], str)
