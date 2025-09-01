import uuid
from typing import Any

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


# ---------------------------------------------------------------------------
# Helper utilities
# ---------------------------------------------------------------------------


def api_get(client, path: str, expected_status: int = 200) -> Any:
    """Issue GET request and return JSON (asserting expected status)."""
    return _request_and_json(client, path, expected_status)


async def _request_and_json(client, path: str, expected_status: int):  # type: ignore
    resp = await client.get(path)
    assert resp.status_code == expected_status, (
        f"{path} -> {resp.status_code} != {expected_status} ({resp.text})"
    )
    return resp.json()


def validate_botanical_group_item(group: dict):
    """Validate a single botanical group structure (shallow)."""
    for key in ["botanical_group_id", "botanical_group_name", "families"]:
        assert key in group
    assert isinstance(group["botanical_group_id"], str)
    assert isinstance(group["botanical_group_name"], str)
    assert isinstance(group["families"], list)


def validate_family_info_basic(data: dict):
    _assert_has_id_and_name(data, "family_id", "family_name")
    assert "botanical_group" in data and isinstance(data["botanical_group"], dict)
    _assert_has_id_and_name(
        data["botanical_group"], "botanical_group_id", "botanical_group_name"
    )
    assert "pests" in data
    assert "diseases" in data


def _assert_has_id_and_name(item: dict, id_field: str = "id", name_field: str = "name"):
    """Assert that a dictionary has the specified ID and name field keys."""
    assert id_field in item and isinstance(item[id_field], str)
    assert name_field in item and isinstance(item[name_field], str)


def _validate_interventions(interventions: list | None):
    """Validate a list of interventions (treatments/preventions)."""
    assert isinstance(interventions, (list, type(None)))
    if interventions:
        for intervention in interventions:
            _assert_has_id_and_name(
                intervention, "intervention_id", "intervention_name"
            )


def _validate_symptoms(symptoms: list | None):
    """Validate a list of symptoms."""
    assert isinstance(symptoms, (list, type(None)))
    if symptoms:
        for symptom in symptoms:
            _assert_has_id_and_name(symptom, "symptom_id", "symptom_name")


def _validate_pests(pests: list | None):
    """Validate the structure of a list of pests."""
    assert isinstance(pests, (list, type(None)))
    if pests:
        for pest in pests:
            _assert_has_id_and_name(pest, "pest_id", "pest_name")
            assert "treatments" in pest
            _validate_interventions(pest.get("treatments"))
            assert "preventions" in pest
            _validate_interventions(pest.get("preventions"))


def _validate_diseases(diseases: list | None):
    """Validate the structure of a list of diseases."""
    assert isinstance(diseases, (list, type(None)))
    if diseases:
        for disease in diseases:
            _assert_has_id_and_name(disease, "disease_id", "disease_name")
            assert "symptoms" in disease
            _validate_symptoms(disease.get("symptoms"))
            assert "treatments" in disease
            _validate_interventions(disease.get("treatments"))
            assert "preventions" in disease
            _validate_interventions(disease.get("preventions"))


class TestListBotanicalGroups:
    @pytest.mark.asyncio
    async def test_list_and_schema(self, client, seed_family_data):
        """Combined success + schema validation for botanical groups."""
        data = await _request_and_json(
            client, f"{PREFIX}/families/botanical-groups/", status.HTTP_200_OK
        )
        assert isinstance(data, list)
        assert data, "Expected at least one seeded group"
        found_seeded = False
        for group in data:
            validate_botanical_group_item(group)
            for fam in group["families"]:
                _assert_has_id_and_name(fam, "family_id", "family_name")
            if group["botanical_group_name"] == seed_family_data["group_name"]:
                found_seeded = True
                fam_names = {f["family_name"] for f in group["families"]}
                assert seed_family_data["family_name"] in fam_names
        assert found_seeded, "Seeded botanical group not found in response"

    @pytest.mark.asyncio
    async def test_list_empty(self, client, mocker):
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )
        data = await _request_and_json(
            client, f"{PREFIX}/families/botanical-groups/", status.HTTP_200_OK
        )
        assert data == []

    @pytest.mark.asyncio
    async def test_unexpected_error(self, client, mocker):
        """Test endpoint returns 500 on unexpected error."""
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            side_effect=Exception("Simulated DB error"),
        )
        response = await client.get(f"{PREFIX}/families/botanical-groups/")
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
                resp = await client.get(f"{PREFIX}/families/botanical-groups/")
                assert resp.status_code == status.HTTP_200_OK, f"Request {i + 1} failed"

            resp_limited = await client.get(f"{PREFIX}/families/botanical-groups/")
            assert resp_limited.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        finally:
            limiter.enabled = original_limiter_enabled
            limiter._storage.reset()

    @pytest.mark.asyncio
    @pytest.mark.asyncio
    @pytest.mark.parametrize("invalid_id", ["not-a-uuid", "12345-not-uuid"])
    async def test_invalid_uuid_format(self, client, invalid_id):
        resp = await client.get(f"{PREFIX}/families/{invalid_id}/info")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        detail = resp.json()["detail"][0]
        assert detail["type"] == "resourcenotfounderror"

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
        response = await client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert len(data) > 0

        assert data[0]["botanical_group_name"] == expected_first


class TestGetFamilyInfo:
    @pytest.mark.asyncio
    async def test_success_and_schema(self, client, seed_family_data):
        """Combine success + schema validation for family info."""
        family_id = str(seed_family_data["family_id"])
        resp = await client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["family_id"] == family_id
        assert data["family_name"] == seed_family_data["family_name"]
        validate_family_info_basic(data)

    @pytest.mark.asyncio
    async def test_not_found(self, client, mocker):
        """Test retrieval of family info for non-existent family returns 404."""
        non_existent_id = str(uuid.uuid4())
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            return_value=None,
        )
        resp = await client.get(f"{PREFIX}/families/{non_existent_id}/info")
        assert resp.status_code == status.HTTP_404_NOT_FOUND
        error_detail = resp.json()["detail"][0]
        assert error_detail["msg"] == f"Family with id {non_existent_id} not found"
        assert error_detail["type"] == "resourcenotfounderror"

    @pytest.mark.asyncio
    async def test_nested_structures_validation(self, client, seed_family_data):
        """Explicit nested structure validation (pests/diseases)."""
        family_id = str(seed_family_data["family_id"])
        resp = await client.get(f"{PREFIX}/families/{family_id}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
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
                family_id=uuid.UUID(family_id_str),
                family_name=seed_family_data["family_name"],
                pests=None,
                diseases=None,
                botanical_group=BotanicalGroupInfoSchema(
                    botanical_group_id=uuid.UUID(botanical_group_id_str),
                    botanical_group_name=seed_family_data["group_name"],
                    rotate_years=2,
                ),
            ),
        )
        resp = await client.get(f"{PREFIX}/families/{family_id_str}/info")
        assert resp.status_code == status.HTTP_200_OK
        data = resp.json()
        assert data["family_id"] == family_id_str
        assert data["family_name"] == seed_family_data["family_name"]
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
        resp = await client.get(f"{PREFIX}/families/{family_id_str}/info")
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
                    family_id=uuid.UUID(family_id_str),
                    family_name="Test Family",
                    pests=None,
                    diseases=None,
                    botanical_group=BotanicalGroupInfoSchema(
                        botanical_group_id=uuid.UUID(mock_botanical_group_id_str),
                        botanical_group_name="Some Group",
                        rotate_years=3,
                    ),
                ),
            )

            for i in range(20):
                resp = await client.get(f"{PREFIX}/families/{family_id_str}/info")
                assert resp.status_code == status.HTTP_200_OK, f"Request {i + 1} failed"

            resp_limited = await client.get(f"{PREFIX}/families/{family_id_str}/info")
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
            family_id=uuid.UUID(family_id),
            family_name="Complete Family",
            botanical_group=BotanicalGroupInfoSchema(
                botanical_group_id=uuid.UUID(botanical_group_id),
                botanical_group_name="Complete Group",
                rotate_years=3,
            ),
            pests=[
                PestSchema(
                    pest_id=uuid.UUID(str(uuid.uuid4())),
                    pest_name="test pest",
                    treatments=[
                        InterventionSchema(
                            intervention_id=uuid.UUID(str(uuid.uuid4())),
                            intervention_name="treatment 1",
                        ),
                        InterventionSchema(
                            intervention_id=uuid.UUID(str(uuid.uuid4())),
                            intervention_name="treatment 2",
                        ),
                    ],
                    preventions=[
                        InterventionSchema(
                            intervention_id=uuid.UUID(str(uuid.uuid4())),
                            intervention_name="prevention 1",
                        ),
                    ],
                )
            ],
            diseases=[
                DiseaseSchema(
                    disease_id=uuid.UUID(str(uuid.uuid4())),
                    disease_name="test disease",
                    symptoms=[
                        SymptomSchema(
                            symptom_id=uuid.UUID(str(uuid.uuid4())),
                            symptom_name="symptom 1",
                        ),
                    ],
                    treatments=[
                        InterventionSchema(
                            intervention_id=uuid.UUID(str(uuid.uuid4())),
                            intervention_name="disease treatment",
                        ),
                    ],
                    preventions=[
                        InterventionSchema(
                            intervention_id=uuid.UUID(str(uuid.uuid4())),
                            intervention_name="disease prevention",
                        ),
                    ],
                )
            ],
            antagonises=[
                FamilyRelationSchema(
                    family_id=uuid.UUID(str(uuid.uuid4())), family_name="antagonist 1"
                ),
            ],
            companion_to=[
                FamilyRelationSchema(
                    family_id=uuid.UUID(str(uuid.uuid4())), family_name="companion 1"
                ),
                FamilyRelationSchema(
                    family_id=uuid.UUID(str(uuid.uuid4())), family_name="companion 2"
                ),
            ],
        )

        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_family_details",
            return_value=mock_data,
        )

        response = await client.get(f"{PREFIX}/families/{family_id}/info")
        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["pests"][0]["treatments"][0]["intervention_name"] == "treatment 1"
        assert data["diseases"][0]["symptoms"][0]["symptom_name"] == "symptom 1"
        assert data["antagonises"][0]["family_name"] == "antagonist 1"
        assert len(data["companion_to"]) == 2


class TestFamilyAPIPerformance:
    """Tests focused on API performance and optimization."""

    @pytest.mark.asyncio
    async def test_response_headers(self, client, seed_family_data):
        """Test that responses include proper headers for caching."""
        family_id = str(seed_family_data["family_id"])
        response = await client.get(f"{PREFIX}/families/{family_id}/info")
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
                families.append(
                    {"family_id": str(uuid.uuid4()), "family_name": f"family_{i}_{j}"}
                )

            large_data.append(
                {
                    "botanical_group_id": str(group_id),
                    "botanical_group_name": f"botanical_group_{i}",
                    "rotate_years": i % 5,
                    "families": families,
                }
            )

        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[BotanicalGroupSchema.model_validate(g) for g in large_data],
        )

        response = await client.get(f"{PREFIX}/families/botanical-groups/")
        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        assert len(data) == 50
        assert len(data[0]["families"]) == 10


class TestInputValidation:
    """Edge cases consolidated (invalid UUID covered above)."""

    @pytest.mark.asyncio
    async def test_empty_botanical_groups_response(self, client, mocker):
        mocker.patch(
            "app.api.services.family.family_unit_of_work.FamilyUnitOfWork.get_all_botanical_groups_with_families",
            return_value=[],
        )
        data = await _request_and_json(
            client, f"{PREFIX}/families/botanical-groups/", status.HTTP_200_OK
        )
        assert data == []
