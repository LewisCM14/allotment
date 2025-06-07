"""
Family API Integration Tests
"""

import uuid

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.schemas.family.family_schema import (
    BotanicalGroupInfoSchema,
    FamilyInfoSchema,
)

PREFIX = settings.API_PREFIX


class TestListBotanicalGroups:
    @pytest.mark.asyncio
    async def test_success(self, client, seed_family_data):
        """Test successful retrieval of botanical groups with families and correct data types."""
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, list)
        found_seeded_group = False
        for group in data:
            assert isinstance(group["id"], str)
            assert isinstance(group["name"], str)
            assert "recommended_rotation_years" in group
            assert isinstance(group["recommended_rotation_years"], (int, type(None)))
            assert isinstance(group["families"], list)
            for fam in group["families"]:
                assert isinstance(fam["id"], str)
                assert isinstance(fam["name"], str)

            if group["name"] == seed_family_data["group_name"]:
                found_seeded_group = True
                assert group["recommended_rotation_years"] == 2
                fam_names = [fam["name"] for fam in group["families"]]
                assert seed_family_data["family_name"] in fam_names
        assert found_seeded_group, "Seeded botanical group not found in response"

    @pytest.mark.asyncio
    async def test_empty_result(self, client, mocker):
        """Test endpoint returns empty list if no botanical groups exist."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []

    @pytest.mark.asyncio
    async def test_schema_validation(self, client, seed_family_data):
        """Test that all botanical groups and families conform to schema."""
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0, "Should have data from seed_family_data"
        for group in data:
            assert "id" in group and isinstance(group["id"], str)
            assert "name" in group and isinstance(group["name"], str)
            assert "recommended_rotation_years" in group
            assert "families" in group and isinstance(group["families"], list)
            for fam in group["families"]:
                assert "id" in fam and isinstance(fam["id"], str)
                assert "name" in fam and isinstance(fam["name"], str)

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client, mocker):
        """Test endpoint returns 500 on unexpected error."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            side_effect=Exception("Simulated DB error"),
        )
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_detail = response.json()["detail"][0]
        assert (
            "an unexpected error occurred while retrieving botanical groups"
            in error_detail["msg"].lower()
        )
        assert error_detail["type"] == "businesslogicerror"

    @pytest.mark.asyncio
    async def test_rate_limit(self, client, mocker):
        """Test rate limiting is enforced (if enabled)."""
        from app.api.core.limiter import limiter

        original_limiter_enabled = limiter.enabled
        try:
            limiter.enabled = True
            limiter._storage.reset()
            mocker.patch(
                "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
                return_value=[],
            )
            for i in range(20):
                resp = client.get(f"{PREFIX}/families/botanical-groups/")
                assert resp.status_code == status.HTTP_200_OK, f"Request {i + 1} failed"

            resp_limited = client.get(f"{PREFIX}/families/botanical-groups/")
            assert resp_limited.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        finally:
            limiter.enabled = original_limiter_enabled
            limiter._storage.reset()


class TestGetFamilyInfo:
    @pytest.mark.asyncio
    async def test_success(self, client, seed_family_data):
        """Test successful retrieval of detailed family info."""
        family_id = str(seed_family_data["family_id"])
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == family_id
        assert data["name"] == seed_family_data["family_name"]
        for field in [
            "pests",
            "diseases",
            "botanical_group",
        ]:
            assert field in data
        assert isinstance(data["pests"], (list, type(None)))
        assert isinstance(data["diseases"], (list, type(None)))
        assert isinstance(data["botanical_group"], dict)

    @pytest.mark.asyncio
    async def test_not_found(self, client, mocker):
        """Test retrieval of family info for non-existent family returns 404."""
        non_existent_id = str(uuid.uuid4())
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            return_value=None,
        )
        resp = client.get(f"{PREFIX}/families/{non_existent_id}/info")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        error_detail = resp.json()["detail"][0]
        assert error_detail["msg"] == f"Family with id {non_existent_id} not found"
        assert error_detail["type"] == "resourcenotfounderror"

    @pytest.mark.asyncio
    async def test_schema_validation(self, client, seed_family_data):
        """Test that the family info endpoint returns data conforming to schema."""
        family_id = str(seed_family_data["family_id"])
        resp = client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert "id" in data and isinstance(data["id"], str)
        assert "name" in data and isinstance(data["name"], str)
        assert "pests" in data
        assert isinstance(data["pests"], (list, type(None)))
        assert "diseases" in data
        assert isinstance(data["diseases"], (list, type(None)))
        assert "botanical_group" in data and isinstance(data["botanical_group"], dict)
        assert "id" in data["botanical_group"] and isinstance(
            data["botanical_group"]["id"], str
        )

        if data.get("pests") is not None:
            for pest in data.get("pests", []):
                assert "id" in pest and isinstance(pest["id"], str)
                assert "name" in pest and isinstance(pest["name"], str)
                assert "treatments" in pest
                assert isinstance(pest["treatments"], (list, type(None)))
                assert "preventions" in pest
                assert isinstance(pest["preventions"], (list, type(None)))

                if pest.get("treatments") is not None:
                    for treatment in pest["treatments"]:
                        assert "id" in treatment and isinstance(treatment["id"], str)
                        assert "name" in treatment and isinstance(
                            treatment["name"], str
                        )

                if pest.get("preventions") is not None:
                    for prevention in pest["preventions"]:
                        assert "id" in prevention and isinstance(prevention["id"], str)
                        assert "name" in prevention and isinstance(
                            prevention["name"], str
                        )

        if data.get("diseases") is not None:
            for disease in data.get("diseases", []):
                assert "id" in disease and isinstance(disease["id"], str)
                assert "name" in disease and isinstance(disease["name"], str)
                assert "symptoms" in disease
                assert isinstance(disease["symptoms"], (list, type(None)))
                assert "treatments" in disease
                assert isinstance(disease["treatments"], (list, type(None)))
                assert "preventions" in disease
                assert isinstance(disease["preventions"], (list, type(None)))

                if disease.get("symptoms") is not None:
                    for symptom in disease["symptoms"]:
                        assert "id" in symptom and isinstance(symptom["id"], str)
                        assert "name" in symptom and isinstance(symptom["name"], str)

                if disease.get("treatments") is not None:
                    for treatment in disease["treatments"]:
                        assert "id" in treatment and isinstance(treatment["id"], str)
                        assert "name" in treatment and isinstance(
                            treatment["name"], str
                        )

                if disease.get("preventions") is not None:
                    for prevention in disease["preventions"]:
                        assert "id" in prevention and isinstance(prevention["id"], str)
                        assert "name" in prevention and isinstance(
                            prevention["name"], str
                        )

    @pytest.mark.asyncio
    async def test_empty_relations(self, client, seed_family_data, mocker):
        """Test family info endpoint when family has no pests, diseases, etc."""
        family_id_str = str(seed_family_data["family_id"])
        botanical_group_id_str = str(seed_family_data["botanical_group_id"])

        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            return_value=FamilyInfoSchema(
                id=uuid.UUID(family_id_str),
                name=seed_family_data["family_name"],
                pests=None,
                diseases=None,
                botanical_group=BotanicalGroupInfoSchema(
                    id=uuid.UUID(botanical_group_id_str),
                    name=seed_family_data["group_name"],
                    recommended_rotation_years=2,
                ),
            ),
        )
        resp = client.get(f"{PREFIX}/families/{family_id_str}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["id"] == family_id_str
        assert data["name"] == seed_family_data["family_name"]
        assert data["pests"] is None
        assert data["diseases"] is None

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client, seed_family_data, mocker):
        """Test error handling for unexpected exceptions in family info endpoint."""
        family_id_str = str(seed_family_data["family_id"])
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            side_effect=Exception("Simulated DB error"),
        )
        resp = client.get(f"{PREFIX}/families/{family_id_str}/info")
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        error_detail = resp.json()["detail"][0]
        assert (
            "an unexpected error occurred while retrieving family information"
            in error_detail["msg"].lower()
        )
        assert error_detail["type"] == "businesslogicerror"

    @pytest.mark.asyncio
    async def test_rate_limit(self, client, seed_family_data, mocker):
        """Test rate limiting is enforced on family info endpoint."""
        from app.api.core.limiter import limiter

        original_limiter_enabled = limiter.enabled
        try:
            limiter.enabled = True
            limiter._storage.reset()
            family_id_str = str(seed_family_data["family_id"])
            mock_botanical_group_id_str = str(uuid.uuid4())

            mocker.patch(
                "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
                return_value=FamilyInfoSchema(
                    id=uuid.UUID(family_id_str),
                    name="Test Family",
                    pests=None,
                    diseases=None,
                    botanical_group=BotanicalGroupInfoSchema(
                        id=uuid.UUID(mock_botanical_group_id_str),
                        name="Some Group",
                        recommended_rotation_years=3,
                    ),
                ),
            )

            for i in range(20):
                resp = client.get(f"{PREFIX}/families/{family_id_str}/info")
                assert resp.status_code == status.HTTP_200_OK, f"Request {i + 1} failed"

            resp_limited = client.get(f"{PREFIX}/families/{family_id_str}/info")
            assert resp_limited.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        finally:
            limiter.enabled = original_limiter_enabled
            limiter._storage.reset()
