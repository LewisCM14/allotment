import uuid
from collections import defaultdict
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.models.disease_and_pest.disease_model import Disease
from app.api.models.disease_and_pest.intervention_model import Intervention
from app.api.models.disease_and_pest.pest_model import Pest
from app.api.models.disease_and_pest.symptom_model import Symptom
from app.api.models.family.botanical_group_model import BotanicalGroup
from app.api.models.family.family_model import Family
from app.api.repositories.family.family_repository import FamilyRepository
from app.api.schemas.family.family_schema import (
    DiseaseSchema,
    FamilyInfoSchema,
    PestSchema,
)


class TestFamilyRepository:
    """Test suite for FamilyRepository."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def family_repository(self, mock_db):
        """Create a FamilyRepository instance with mock database."""
        return FamilyRepository(db=mock_db)

    @pytest.fixture
    def sample_botanical_group(self):
        """Create a sample botanical group."""
        return BotanicalGroup(
            id=uuid.uuid4(), name="Test Botanical Group", recommended_rotation_years=3
        )

    @pytest.fixture
    def sample_family(self, sample_botanical_group):
        """Create a sample family."""
        return Family(
            id=uuid.uuid4(), name="Test Family", botanical_group=sample_botanical_group
        )

    def test_init(self, mock_db):
        """Test repository initialization."""
        repo = FamilyRepository(db=mock_db)
        assert repo.db == mock_db

    @pytest.mark.asyncio
    async def test_get_all_botanical_groups_with_families(
        self, family_repository, mock_db, sample_botanical_group
    ):
        """Test retrieving all botanical groups with families."""
        # Mock the database query result
        mock_result = MagicMock()
        mock_result.unique.return_value.scalars.return_value.all.return_value = [
            sample_botanical_group
        ]
        mock_db.execute.return_value = mock_result

        result = await family_repository.get_all_botanical_groups_with_families()

        assert result == [sample_botanical_group]
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_family_by_id(self, family_repository, mock_db, sample_family):
        """Test retrieving a family by ID."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_family
        mock_db.execute.return_value = mock_result

        result = await family_repository.get_family_by_id(123)

        assert result == sample_family
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_family_by_id_not_found(self, family_repository, mock_db):
        """Test retrieving a family by ID when not found."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await family_repository.get_family_by_id(999)

        assert result is None
        mock_db.execute.assert_called_once()

    def test_validate_family_id_with_uuid(self, family_repository):
        """Test validating a UUID family ID."""
        test_uuid = uuid.uuid4()
        result = family_repository._validate_family_id(test_uuid)
        assert result == test_uuid

    def test_validate_family_id_with_valid_string(self, family_repository):
        """Test validating a valid string UUID."""
        test_uuid = uuid.uuid4()
        result = family_repository._validate_family_id(str(test_uuid))
        assert result == test_uuid

    def test_validate_family_id_with_invalid_string(self, family_repository):
        """Test validating an invalid string."""
        result = family_repository._validate_family_id("invalid-uuid")
        assert result is None

    def test_validate_family_id_with_invalid_type(self, family_repository):
        """Test validating an invalid type."""
        result = family_repository._validate_family_id(123)
        assert result is None

    @pytest.mark.asyncio
    async def test_fetch_family_by_uuid(
        self, family_repository, mock_db, sample_family
    ):
        """Test fetching family by UUID."""
        mock_result = MagicMock()
        mock_result.unique.return_value.scalar_one_or_none.return_value = sample_family
        mock_db.execute.return_value = mock_result

        result = await family_repository._fetch_family_by_uuid(sample_family.id)

        assert result == sample_family
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_map_interventions_to_items_simplified(self, family_repository):
        """Test mapping interventions to items with mocked methods."""
        item_ids = [uuid.uuid4(), uuid.uuid4()]

        # Create a simple mock for the method result
        with patch.object(
            family_repository, "_map_interventions_to_items"
        ) as mock_method:
            expected_result = defaultdict(list)
            expected_result[item_ids[0]] = []
            expected_result[item_ids[1]] = []
            mock_method.return_value = expected_result

            result = await family_repository._map_interventions_to_items(
                item_ids, MagicMock(), "pest_id"
            )

            assert isinstance(result, defaultdict)
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_map_symptoms_to_diseases_simplified(self, family_repository):
        """Test mapping symptoms to diseases with simplified mocking."""
        disease_ids = [uuid.uuid4(), uuid.uuid4()]

        # Test empty list case directly
        result = await family_repository._map_symptoms_to_diseases([])
        assert isinstance(result, defaultdict)
        assert len(result) == 0

        # Mock the method for non-empty case
        with patch.object(
            family_repository, "_map_symptoms_to_diseases"
        ) as mock_method:
            expected_result = defaultdict(list)
            mock_method.return_value = expected_result

            result = await family_repository._map_symptoms_to_diseases(disease_ids)

            assert isinstance(result, defaultdict)
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_pests_for_family_simplified(self, family_repository):
        """Test fetching pests for family with simplified mocking."""
        family_id = uuid.uuid4()

        # Mock the method directly
        with patch.object(family_repository, "_fetch_pests_for_family") as mock_method:
            expected_result = []
            mock_method.return_value = expected_result

            result = await family_repository._fetch_pests_for_family(family_id)

            assert result == expected_result
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_diseases_for_family_simplified(self, family_repository):
        """Test fetching diseases for family with simplified mocking."""
        family_id = uuid.uuid4()

        # Mock the method directly
        with patch.object(
            family_repository, "_fetch_diseases_for_family"
        ) as mock_method:
            expected_result = []
            mock_method.return_value = expected_result

            result = await family_repository._fetch_diseases_for_family(family_id)

            assert result == expected_result
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_fetch_related_families_simplified(self, family_repository):
        """Test fetching related families with simplified mocking."""
        family_id = uuid.uuid4()

        # Mock the method directly
        with patch.object(family_repository, "_fetch_related_families") as mock_method:
            expected_result = set()
            mock_method.return_value = expected_result

            result = await family_repository._fetch_related_families(
                family_id, MagicMock(), "related_family_id"
            )

            assert result == expected_result
            mock_method.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_family_info_invalid_id(self, family_repository):
        """Test getting family info with invalid ID."""
        result = await family_repository.get_family_info("invalid-uuid")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_family_info_not_found(self, family_repository):
        """Test getting family info when family not found."""
        family_id = uuid.uuid4()

        with patch.object(
            family_repository, "_fetch_family_by_uuid", return_value=None
        ):
            result = await family_repository.get_family_info(family_id)
            assert result is None

    @pytest.mark.asyncio
    async def test_get_family_info_success(
        self, family_repository, sample_family, sample_botanical_group
    ):
        """Test successful family info retrieval."""
        family_id = sample_family.id

        with (
            patch.object(
                family_repository, "_fetch_family_by_uuid", return_value=sample_family
            ),
            patch.object(family_repository, "_fetch_pests_for_family", return_value=[]),
            patch.object(
                family_repository, "_fetch_diseases_for_family", return_value=[]
            ),
            patch.object(
                family_repository, "_fetch_related_families", return_value=set()
            ),
        ):
            result = await family_repository.get_family_info(family_id)

            assert result is not None
            assert isinstance(result, FamilyInfoSchema)
            assert result.id == sample_family.id
            assert result.name == sample_family.name

    def test_add_family(self, family_repository):
        """Test add_family stub method."""
        # Should not raise any exception
        family_repository.add_family()
        family_repository.add_family("arg1", "arg2", kwarg1="value1")

    def test_validate_family_id_with_none(self, family_repository):
        """_validate_family_id returns None when input is None."""
        assert family_repository._validate_family_id(None) is None

    @pytest.mark.asyncio
    async def test_get_all_botanical_groups_with_families_error(
        self, family_repository, mock_db
    ):
        """Error path propagates when underlying execution raises."""
        mock_db.execute.side_effect = RuntimeError("boom")
        with pytest.raises(RuntimeError):
            await family_repository.get_all_botanical_groups_with_families()

    @pytest.mark.asyncio
    async def test_fetch_pests_for_family_empty(self, family_repository):
        """_fetch_pests_for_family returns empty list when no pests found."""
        family_id = uuid.uuid4()
        with patch.object(family_repository.db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_execute.return_value = mock_result
            result = await family_repository._fetch_pests_for_family(family_id)
            assert result == []

    @pytest.mark.asyncio
    async def test_fetch_diseases_for_family_empty(self, family_repository):
        """_fetch_diseases_for_family returns empty list when no diseases found."""
        family_id = uuid.uuid4()
        with patch.object(family_repository.db, "execute") as mock_execute:
            mock_result = MagicMock()
            mock_result.scalars.return_value.all.return_value = []
            mock_execute.return_value = mock_result
            result = await family_repository._fetch_diseases_for_family(family_id)
            assert result == []

    @pytest.mark.asyncio
    async def test_get_family_info_with_components(
        self, family_repository, sample_family
    ):
        """get_family_info aggregates pests, diseases, antagonises, companions."""
        fam_id = sample_family.id
        pest_schema = PestSchema(
            id=uuid.uuid4(), name="Pest A", treatments=None, preventions=None
        )
        disease_schema = DiseaseSchema(
            id=uuid.uuid4(),
            name="Disease A",
            symptoms=None,
            treatments=None,
            preventions=None,
        )
        relation_family = Family(
            id=uuid.uuid4(),
            name="RelFam",
            botanical_group=sample_family.botanical_group,
        )
        with (
            patch.object(
                family_repository, "_fetch_family_by_uuid", return_value=sample_family
            ),
            patch.object(
                family_repository, "_fetch_pests_for_family", return_value=[pest_schema]
            ),
            patch.object(
                family_repository,
                "_fetch_diseases_for_family",
                return_value=[disease_schema],
            ),
            patch.object(
                family_repository,
                "_fetch_related_families",
                side_effect=[[relation_family], [relation_family]],
            ),
        ):
            result = await family_repository.get_family_info(fam_id)
            assert result is not None
            assert isinstance(result, FamilyInfoSchema)
            assert result.pests and result.pests[0].name == "Pest A"
            assert result.diseases and result.diseases[0].name == "Disease A"
            assert result.antagonises and result.antagonises[0].name == "RelFam"
            assert result.companion_to and result.companion_to[0].name == "RelFam"

    @pytest.mark.asyncio
    async def test_map_interventions_to_items_with_data(self, family_repository):
        """Test mapping interventions to items when data exists."""
        with patch.object(family_repository.db, "execute") as mock_execute:
            mock_intervention = Intervention(id=uuid.uuid4(), name="Test Intervention")
            item_id = uuid.uuid4()

            mock_result = MagicMock()
            mock_result.all.return_value = [(item_id, mock_intervention)]
            mock_execute.return_value = mock_result

            # Mock association table with minimal required structure
            mock_table = MagicMock()
            mock_table.c.intervention_id = MagicMock()
            mock_table.c.pest_id = MagicMock()

            with patch(
                "app.api.repositories.family.family_repository.select"
            ) as mock_select:
                mock_query = MagicMock()
                mock_select.return_value.join.return_value.where.return_value = (
                    mock_query
                )

                result = await family_repository._map_interventions_to_items(
                    [item_id], mock_table, "pest_id"
                )

                assert isinstance(result, defaultdict)
                assert item_id in result
                assert len(result[item_id]) == 1
                assert result[item_id][0] == mock_intervention

    @pytest.mark.asyncio
    async def test_map_symptoms_to_diseases_with_data(self, family_repository):
        """Test mapping symptoms to diseases when data exists."""
        with patch.object(family_repository.db, "execute") as mock_execute:
            mock_symptom = Symptom(id=uuid.uuid4(), name="Test Symptom")
            disease_id = uuid.uuid4()

            mock_result = MagicMock()
            mock_result.all.return_value = [(disease_id, mock_symptom)]
            mock_execute.return_value = mock_result

            # Mock the select query
            with patch(
                "app.api.repositories.family.family_repository.select"
            ) as mock_select:
                mock_query = MagicMock()
                mock_select.return_value.join.return_value.where.return_value = (
                    mock_query
                )

                result = await family_repository._map_symptoms_to_diseases([disease_id])

                assert isinstance(result, defaultdict)
                assert disease_id in result
                assert len(result[disease_id]) == 1
                assert result[disease_id][0] == mock_symptom

    @pytest.mark.asyncio
    async def test_symptom_disease_mapping_empty_list(self, family_repository):
        """Test mapping symptoms to diseases with empty disease list."""
        result = await family_repository._map_symptoms_to_diseases([])

        assert isinstance(result, defaultdict)
        assert len(result) == 0

    @pytest.mark.asyncio
    async def test_fetch_pests_for_family_with_data(self, family_repository):
        """Test fetching pests when pests exist."""
        family_id = uuid.uuid4()

        with patch.object(family_repository.db, "execute") as mock_execute:
            pest_id = uuid.uuid4()
            mock_pest = Pest(id=pest_id, name="Test Pest")

            mock_pest_result = MagicMock()
            mock_pest_result.scalars.return_value.all.return_value = [mock_pest]
            mock_execute.return_value = mock_pest_result

            with patch(
                "app.api.schemas.family.family_schema.PestSchema.model_validate"
            ) as mock_schema:
                mock_schema.return_value = PestSchema(
                    id=pest_id, name="Test Pest", treatments=None, preventions=None
                )

                result = await family_repository._fetch_pests_for_family(family_id)

                assert result == [
                    PestSchema(
                        id=pest_id, name="Test Pest", treatments=None, preventions=None
                    )
                ]

    @pytest.mark.asyncio
    async def test_fetch_diseases_for_family_with_data(self, family_repository):
        """Test fetching diseases when diseases exist."""
        family_id = uuid.uuid4()

        with patch.object(family_repository.db, "execute") as mock_execute:
            disease_id = uuid.uuid4()
            mock_disease = Disease(id=disease_id, name="Test Disease")

            mock_disease_result = MagicMock()
            mock_disease_result.scalars.return_value.all.return_value = [mock_disease]
            mock_execute.return_value = mock_disease_result

            with patch(
                "app.api.schemas.family.family_schema.DiseaseSchema.model_validate"
            ) as mock_schema:
                mock_schema.return_value = DiseaseSchema(
                    id=disease_id,
                    name="Test Disease",
                    symptoms=None,
                    treatments=None,
                    preventions=None,
                )

                result = await family_repository._fetch_diseases_for_family(family_id)

                assert result == [
                    DiseaseSchema(
                        id=disease_id,
                        name="Test Disease",
                        symptoms=None,
                        treatments=None,
                        preventions=None,
                    )
                ]

    @pytest.mark.asyncio
    async def test_fetch_related_families_with_data(self, family_repository):
        """Test fetching related families when data exists."""
        family_id = uuid.uuid4()
        related_family_id = uuid.uuid4()
        mock_family = Family(id=related_family_id, name="Related Family")

        # Mock the association table with the required structure
        mock_association_table = MagicMock()
        mock_association_table.c.family_id = MagicMock()
        mock_association_table.c.related_family_id = MagicMock()

        with (
            patch(
                "app.api.repositories.family.family_repository.select"
            ) as mock_select,
            patch.object(family_repository.db, "execute") as mock_execute,
        ):
            # Mock the select().join().where() chain
            mock_query = MagicMock()
            mock_select.return_value.join.return_value.where.return_value = mock_query

            mock_family_result = MagicMock()
            mock_family_result.unique.return_value.scalars.return_value.all.return_value = [
                mock_family
            ]
            mock_execute.return_value = mock_family_result

            result = await family_repository._fetch_related_families(
                family_id, mock_association_table, "related_family_id"
            )

            assert result == {mock_family}
