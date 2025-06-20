"""
Family API Integration Tests
"""

import uuid

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.schemas.family.family_schema import (
    BotanicalGroupInfoSchema,
    BotanicalGroupSchema,
    DiseaseSchema,
    FamilyInfoSchema,
    FamilyRelationSchema,
    InterventionSchema,
    PestSchema,
    SymptomSchema,
)

PREFIX = settings.API_PREFIX


def _assert_has_id_and_name(item: dict):
    """Assert that a dictionary has 'id' (string) and 'name' (string) keys."""
    assert "id" in item and isinstance(item["id"], str)
    assert "name" in item and isinstance(item["name"], str)


def _validate_interventions(interventions: list | None):
    """Validate a list of interventions (treatments/preventions)."""
    assert isinstance(interventions, (list, type(None)))
    if interventions:
        for intervention in interventions:
            _assert_has_id_and_name(intervention)


def _validate_symptoms(symptoms: list | None):
    """Validate a list of symptoms."""
    assert isinstance(symptoms, (list, type(None)))
    if symptoms:
        for symptom in symptoms:
            _assert_has_id_and_name(symptom)


def _validate_pests(pests: list | None):
    """Validate the structure of a list of pests."""
    assert isinstance(pests, (list, type(None)))
    if pests:
        for pest in pests:
            _assert_has_id_and_name(pest)
            assert "treatments" in pest
            _validate_interventions(pest.get("treatments"))
            assert "preventions" in pest
            _validate_interventions(pest.get("preventions"))


def _validate_diseases(diseases: list | None):
    """Validate the structure of a list of diseases."""
    assert isinstance(diseases, (list, type(None)))
    if diseases:
        for disease in diseases:
            _assert_has_id_and_name(disease)
            assert "symptoms" in disease
            _validate_symptoms(disease.get("symptoms"))
            assert "treatments" in disease
            _validate_interventions(disease.get("treatments"))
            assert "preventions" in disease
            _validate_interventions(disease.get("preventions"))


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

    @pytest.mark.asyncio
    async def test_invalid_uuid_format(self, client):
        """Test that invalid UUID format returns a proper error response."""
        invalid_id = "not-a-uuid"
        response = client.get(f"{PREFIX}/families/{invalid_id}/info")
        assert response.status_code == status.HTTP_404_NOT_FOUND
        error_detail = response.json()["detail"][0]
        assert "not found" in error_detail["msg"].lower()
        assert error_detail["type"] == "resourcenotfounderror"

    @pytest.mark.asyncio
    @pytest.mark.parametrize(
        "order_by,expected_first",
        [
            ("name", "testgroup"),
        ],
    )
    async def test_botanical_groups_ordering(
        self, client, seed_family_data, order_by, expected_first
    ):
        """Test that botanical groups are returned in the correct order."""
        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

        assert data[0]["name"] == expected_first


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

        # Validate base family info
        _assert_has_id_and_name(data)
        assert "botanical_group" in data and isinstance(data["botanical_group"], dict)
        _assert_has_id_and_name(data["botanical_group"])

        # Validate nested structures
        _validate_pests(data.get("pests"))
        _validate_diseases(data.get("diseases"))

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

    @pytest.mark.asyncio
    async def test_family_full_relations(self, client, mocker):
        """Test family info when all relationships are populated."""
        family_id = str(uuid.uuid4())
        botanical_group_id = str(uuid.uuid4())

        mock_data = FamilyInfoSchema(
            id=uuid.UUID(family_id),
            name="Complete Family",
            botanical_group=BotanicalGroupInfoSchema(
                id=uuid.UUID(botanical_group_id),
                name="Complete Group",
                recommended_rotation_years=3,
            ),
            pests=[
                PestSchema(
                    id=uuid.UUID(str(uuid.uuid4())),
                    name="test pest",
                    treatments=[
                        InterventionSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="treatment 1"
                        ),
                        InterventionSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="treatment 2"
                        ),
                    ],
                    preventions=[
                        InterventionSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="prevention 1"
                        ),
                    ],
                )
            ],
            diseases=[
                DiseaseSchema(
                    id=uuid.UUID(str(uuid.uuid4())),
                    name="test disease",
                    symptoms=[
                        SymptomSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="symptom 1"
                        ),
                    ],
                    treatments=[
                        InterventionSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="disease treatment"
                        ),
                    ],
                    preventions=[
                        InterventionSchema(
                            id=uuid.UUID(str(uuid.uuid4())), name="disease prevention"
                        ),
                    ],
                )
            ],
            antagonises=[
                FamilyRelationSchema(
                    id=uuid.UUID(str(uuid.uuid4())), name="antagonist 1"
                ),
            ],
            companion_to=[
                FamilyRelationSchema(
                    id=uuid.UUID(str(uuid.uuid4())), name="companion 1"
                ),
                FamilyRelationSchema(
                    id=uuid.UUID(str(uuid.uuid4())), name="companion 2"
                ),
            ],
        )

        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            return_value=mock_data,
        )

        response = client.get(f"{PREFIX}/families/{family_id}/info")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["pests"][0]["treatments"][0]["name"] == "treatment 1"
        assert data["diseases"][0]["symptoms"][0]["name"] == "symptom 1"
        assert data["antagonises"][0]["name"] == "antagonist 1"
        assert len(data["companion_to"]) == 2


class TestFamilyAPIPerformance:
    """Tests focused on API performance and optimization."""

    @pytest.mark.asyncio
    async def test_response_headers(self, client, seed_family_data):
        """Test that responses include proper headers for caching."""
        family_id = str(seed_family_data["family_id"])
        response = client.get(f"{PREFIX}/families/{family_id}/info")
        assert response.status_code == status.HTTP_200_OK

        assert "X-Request-ID" in response.headers

    @pytest.mark.asyncio
    async def test_large_response_handling(self, client, mocker):
        """Test handling of large response data."""
        large_data = []
        for i in range(50):
            group_id = uuid.uuid4()
            families = []
            for j in range(10):
                families.append({"id": str(uuid.uuid4()), "name": f"family_{i}_{j}"})

            large_data.append(
                {
                    "id": str(group_id),
                    "name": f"botanical_group_{i}",
                    "recommended_rotation_years": i % 5,
                    "families": families,
                }
            )

        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[BotanicalGroupSchema.model_validate(g) for g in large_data],
        )

        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 50
        assert len(data[0]["families"]) == 10


class TestInputValidation:
    """Tests for input validation edge cases."""

    @pytest.mark.asyncio
    async def test_malformed_uuid(self, client):
        """Test handling of malformed UUIDs."""
        malformed_uuid = "12345-not-uuid"
        response = client.get(f"{PREFIX}/families/{malformed_uuid}/info")
        assert response.status_code == status.HTTP_404_NOT_FOUND

    @pytest.mark.asyncio
    async def test_empty_botanical_groups_response(self, client, mocker):
        """Test empty response handling."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )

        response = client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        assert response.json() == []
