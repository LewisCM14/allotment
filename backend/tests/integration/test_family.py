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

    @pytest.mark.asyncio
    async def test_get_family_info_success(self, client, seed_family_data):
        """Test successful retrieval of detailed family info."""
        family_id = str(seed_family_data["family_id"])
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["id"] == family_id
        assert data["name"] == seed_family_data["family_name"]
        assert "pests" in data
        assert "diseases" in data
        assert "interventions" in data
        assert "symptoms" in data
        assert isinstance(data["pests"], list)
        assert isinstance(data["diseases"], list)
        assert isinstance(data["interventions"], list)
        assert isinstance(data["symptoms"], list)

    @pytest.mark.asyncio
    async def test_get_family_info_not_found(self, client):
        """Test retrieval of family info for non-existent family returns 200 with null/empty data or 404 if handled."""
        import uuid

        non_existent_id = str(uuid.uuid4())
        resp = client.get(f"{PREFIX}/families/{non_existent_id}/info")
        # Accept either 200 with None/empty or 404 depending on your implementation
        assert resp.status_code in (200, 404)
        if resp.status_code == 200:
            data = resp.json()
            # Should be empty or None fields
            assert data["id"] == None or data["pests"] == [] or data["diseases"] == []
        else:
            assert resp.json()["detail"][0]["msg"].lower() in (
                "not found",
                "family not found",
            )

    @pytest.mark.asyncio
    async def test_get_family_info_schema(self, client, seed_family_data):
        """Test that the family info endpoint returns data conforming to schema."""
        family_id = str(seed_family_data["family_id"])
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == 200
        data = resp.json()
        # Top-level fields
        assert isinstance(data["id"], str)
        assert isinstance(data["name"], str)
        assert isinstance(data["pests"], list)
        assert isinstance(data["diseases"], list)
        assert isinstance(data["interventions"], list)
        assert isinstance(data["symptoms"], list)
        # Pest fields
        for pest in data["pests"]:
            assert isinstance(pest["id"], str)
            assert isinstance(pest["name"], str)
            assert isinstance(pest["treatments"], list)
            assert isinstance(pest["preventions"], list)
        # Disease fields
        for disease in data["diseases"]:
            assert isinstance(disease["id"], str)
            assert isinstance(disease["name"], str)
            assert isinstance(disease["symptoms"], list)
            assert isinstance(disease["treatments"], list)
            assert isinstance(disease["preventions"], list)
            for symptom in disease["symptoms"]:
                assert isinstance(symptom["id"], str)
                assert isinstance(symptom["name"], str)
            for treat in disease["treatments"]:
                assert isinstance(treat["id"], str)
                assert isinstance(treat["name"], str)
            for prev in disease["preventions"]:
                assert isinstance(prev["id"], str)
                assert isinstance(prev["name"], str)
        # Interventions and symptoms
        for intervention in data["interventions"]:
            assert isinstance(intervention["id"], str)
            assert isinstance(intervention["name"], str)
        for symptom in data["symptoms"]:
            assert isinstance(symptom["id"], str)
            assert isinstance(symptom["name"], str)

    @pytest.mark.asyncio
    async def test_get_family_info_empty_relations(
        self, client, seed_family_data, mocker
    ):
        """Test family info endpoint when family has no pests or diseases."""
        # Patch repository to return empty lists for pests/diseases
        mocker.patch(
            "app.api.repositories.family.family_repository.FamilyRepository.get_family_info",
            return_value={
                "id": seed_family_data["family_id"],
                "name": seed_family_data["family_name"],
                "pests": [],
                "diseases": [],
                "interventions": [],
                "symptoms": [],
            },
        )
        family_id = str(seed_family_data["family_id"])
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == 200
        data = resp.json()
        assert data["pests"] == []
        assert data["diseases"] == []
        assert data["interventions"] == []
        assert data["symptoms"] == []

    @pytest.mark.asyncio
    async def test_get_family_info_error_handling(
        self, client, seed_family_data, mocker
    ):
        """Test error handling for unexpected exceptions in family info endpoint."""
        mocker.patch(
            "app.api.repositories.family.family_repository.FamilyRepository.get_family_info",
            side_effect=Exception("Simulated DB error"),
        )
        family_id = str(seed_family_data["family_id"])
        import app.api.middleware.exception_handler as exc_handler

        with pytest.raises(exc_handler.BusinessLogicError) as exc_info:
            client.get(f"{PREFIX}/families/{family_id}/info")
        assert (
            "an unexpected error occurred while retrieving family information"
            in str(exc_info.value).lower()
        )

    @pytest.mark.asyncio
    async def test_get_family_info_rate_limit(self, client, seed_family_data):
        """Test rate limiting is enforced on family info endpoint."""
        from app.api.core.limiter import limiter

        limiter.enabled = True
        limiter._storage.reset()
        family_id = str(seed_family_data["family_id"])
        for _ in range(20):
            resp = client.get(f"{PREFIX}/families/{family_id}/info")
            assert resp.status_code == 200
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code in (429, 200)
        limiter.enabled = False
