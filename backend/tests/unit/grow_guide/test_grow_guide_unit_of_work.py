"""
Unit tests for GrowGuideUnitOfWork
"""

import uuid
from unittest.mock import AsyncMock

import pytest
from sqlalchemy.exc import IntegrityError

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    DatabaseIntegrityError,
    ResourceNotFoundError,
)
from app.api.schemas.grow_guide.variety_schema import VarietyCreate, VarietyUpdate
from app.api.services.grow_guide.grow_guide_unit_of_work import GrowGuideUnitOfWork
from tests.test_helpers import (
    build_sample_feeds,
    build_week_days,
    make_variety,
)


class TestGrowGuideUnitOfWorkContextManager:
    """Test the async context manager functionality."""

    @pytest.fixture
    def uow(self, mock_db):
        """Create a GrowGuideUnitOfWork instance."""
        return GrowGuideUnitOfWork(mock_db)

    async def test_aenter_returns_self(self, uow, mocker):
        """Test that __aenter__ returns self and logs correctly."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )

        result = await uow.__aenter__()

        assert result is uow
        mock_logger.debug.assert_called_once_with(
            "Starting grow guide unit of work",
            request_id=uow.request_id,
            transaction="begin",
        )

    async def test_aexit_with_no_exception_commits(self, uow, mocker):
        """Test that __aexit__ commits when no exception occurs."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        await uow.__aexit__(None, None, None)

        uow.db.commit.assert_called_once()
        mock_log_timing.assert_called_once_with("db_commit")
        mock_logger.debug.assert_called_once_with(
            "Transaction committed successfully",
            transaction="commit",
            request_id=uow.request_id,
        )

    async def test_aexit_with_exception_rolls_back(self, uow, mocker):
        """Test that __aexit__ rolls back when an exception occurs."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )

        await uow.__aexit__(ValueError, ValueError("test error"), None)

        uow.db.rollback.assert_called_once()
        mock_logger.warning.assert_called_once()
        mock_logger.debug.assert_called_once_with(
            "Transaction rolled back",
            transaction="rollback",
            request_id=uow.request_id,
        )

    async def test_aexit_with_integrity_error_on_commit(self, uow, mocker):
        """Test that __aexit__ handles IntegrityError on commit."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        uow.db.commit.side_effect = IntegrityError("statement", "params", "orig")

        with pytest.raises(DatabaseIntegrityError):
            await uow.__aexit__(None, None, None)

        mock_logger.error.assert_called_once()

    async def test_aexit_with_exception_value_none(self, uow, mocker):
        """Test __aexit__ handles case where exc_value is None."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )

        await uow.__aexit__(ValueError, None, None)

        uow.db.rollback.assert_called_once()
        mock_logger.warning.assert_called_once()


class TestGrowGuideUnitOfWorkRepositoryMethods:
    """Test the repository coordination methods."""

    @pytest.fixture
    def uow(self, mock_db):
        """Create a GrowGuideUnitOfWork instance with mocked repositories."""
        uow = GrowGuideUnitOfWork(mock_db)
        uow.day_repo = AsyncMock()
        uow.variety_repo = AsyncMock()
        uow.week_repo = AsyncMock()
        uow.month_repo = AsyncMock()
        uow.family_repo = AsyncMock()
        return uow

    async def test_get_all_feeds(self, uow, mocker):
        """Test get_all_feeds delegates to variety repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        feeds = build_sample_feeds()
        uow.variety_repo.get_all_feeds.return_value = feeds

        result = await uow.get_all_feeds()

        assert result == feeds
        uow.variety_repo.get_all_feeds.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_feeds", request_id=uow.request_id
        )

    async def test_get_all_days(self, uow, mocker):
        """Test get_all_days delegates to day repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        days = build_week_days()
        uow.day_repo.get_all_days.return_value = days

        result = await uow.get_all_days()

        assert result == days
        uow.day_repo.get_all_days.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_days", request_id=uow.request_id
        )

    async def test_get_all_weeks(self, uow, mocker):
        """Test get_all_weeks delegates to week repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        weeks = [AsyncMock() for _ in range(52)]
        uow.week_repo.get_all_weeks.return_value = weeks

        result = await uow.get_all_weeks()

        assert result == weeks
        uow.week_repo.get_all_weeks.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_weeks", request_id=uow.request_id
        )

    async def test_get_all_months(self, uow, mocker):
        """Test get_all_months delegates to month repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        months = [AsyncMock() for _ in range(12)]
        uow.month_repo.get_all_months.return_value = months

        result = await uow.get_all_months()

        assert result == months
        uow.month_repo.get_all_months.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_months", request_id=uow.request_id
        )

    async def test_get_all_frequencies(self, uow, mocker):
        """Test get_all_frequencies delegates to variety repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        frequencies = [AsyncMock() for _ in range(3)]
        uow.variety_repo.get_all_frequencies.return_value = frequencies

        result = await uow.get_all_frequencies()

        assert result == frequencies
        uow.variety_repo.get_all_frequencies.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_frequencies", request_id=uow.request_id
        )

    async def test_get_all_lifecycles(self, uow, mocker):
        """Test get_all_lifecycles delegates to variety repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        lifecycles = [AsyncMock() for _ in range(2)]
        uow.variety_repo.get_all_lifecycles.return_value = lifecycles

        result = await uow.get_all_lifecycles()

        assert result == lifecycles
        uow.variety_repo.get_all_lifecycles.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_lifecycles", request_id=uow.request_id
        )

    async def test_get_all_planting_conditions(self, uow, mocker):
        """Test get_all_planting_conditions delegates to variety repository."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        conditions = [AsyncMock() for _ in range(3)]
        uow.variety_repo.get_all_planting_conditions.return_value = conditions

        result = await uow.get_all_planting_conditions()

        assert result == conditions
        uow.variety_repo.get_all_planting_conditions.assert_called_once()
        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_all_planting_conditions", request_id=uow.request_id
        )

    async def test_get_variety_options(self, uow, mocker):
        """Test get_variety_options coordinates multiple repositories."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        # Setup mock returns
        lifecycles = [AsyncMock()]
        planting_conditions = [AsyncMock()]
        frequencies = [AsyncMock()]
        feeds = build_sample_feeds()
        weeks = [AsyncMock()]
        families = [AsyncMock()]

        uow.variety_repo.get_all_lifecycles.return_value = lifecycles
        uow.variety_repo.get_all_planting_conditions.return_value = planting_conditions
        uow.variety_repo.get_all_frequencies.return_value = frequencies
        uow.variety_repo.get_all_feeds.return_value = feeds
        uow.week_repo.get_all_weeks.return_value = weeks
        uow.family_repo.get_all_families.return_value = families

        result = await uow.get_variety_options()

        assert result == {
            "lifecycles": lifecycles,
            "planting_conditions": planting_conditions,
            "frequencies": frequencies,
            "feeds": feeds,
            "weeks": weeks,
            "families": families,
        }

        # Verify all repositories were called
        uow.variety_repo.get_all_lifecycles.assert_called_once()
        uow.variety_repo.get_all_planting_conditions.assert_called_once()
        uow.variety_repo.get_all_frequencies.assert_called_once()
        uow.variety_repo.get_all_feeds.assert_called_once()
        uow.week_repo.get_all_weeks.assert_called_once()
        uow.family_repo.get_all_families.assert_called_once()

        mock_logger.info.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "uow_get_variety_options", request_id=uow.request_id
        )


class TestGrowGuideUnitOfWorkVarietyCRUD:
    """Test variety CRUD operations."""

    @pytest.fixture
    def uow(self, mock_db):
        """Create a GrowGuideUnitOfWork instance with mocked repositories."""
        uow = GrowGuideUnitOfWork(mock_db)
        uow.variety_repo = AsyncMock()
        return uow

    @pytest.fixture
    def variety_create_data(self):
        """Sample variety creation data."""
        return VarietyCreate(
            variety_name="Test Tomato",
            family_id=uuid.uuid4(),
            lifecycle_id=uuid.uuid4(),
            sow_week_start_id=uuid.uuid4(),
            sow_week_end_id=uuid.uuid4(),
            planting_conditions_id=uuid.uuid4(),
            soil_ph=6.5,
            plant_depth_cm=2,
            plant_space_cm=30,
            water_frequency_id=uuid.uuid4(),
            high_temp_water_frequency_id=uuid.uuid4(),
            harvest_week_start_id=uuid.uuid4(),
            harvest_week_end_id=uuid.uuid4(),
            is_public=False,
            water_days=[],
        )

    @pytest.fixture
    def user_id(self):
        """Sample user ID."""
        return uuid.uuid4()

    async def test_create_variety_success(
        self, uow, variety_create_data, user_id, mocker
    ):
        """Test successful variety creation."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        # Setup mocks
        uow.variety_repo.variety_name_exists_for_user.return_value = False
        created_variety = make_variety(user_id)
        mock_factory.create_variety.return_value = created_variety
        uow.variety_repo.create_variety.return_value = created_variety

        result = await uow.create_variety(variety_create_data, user_id)

        assert result == created_variety
        uow.variety_repo.variety_name_exists_for_user.assert_called_once_with(
            user_id, variety_create_data.variety_name
        )
        mock_factory.create_variety.assert_called_once_with(
            variety_create_data, user_id
        )
        uow.variety_repo.create_variety.assert_called_once_with(created_variety)
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_create_variety", request_id=uow.request_id
        )

    async def test_create_variety_name_exists(
        self, uow, variety_create_data, user_id, mocker
    ):
        """Test variety creation fails when name already exists."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        uow.variety_repo.variety_name_exists_for_user.return_value = True

        with pytest.raises(BusinessLogicError) as exc_info:
            await uow.create_variety(variety_create_data, user_id)

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.message)
        mock_logger.info.assert_called()

    async def test_create_variety_with_water_days(
        self, uow, variety_create_data, user_id, mocker
    ):
        """Test variety creation with water days."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        # Add water days to test data
        from app.api.schemas.grow_guide.variety_schema import VarietyWaterDayCreate

        variety_create_data.water_days = [
            VarietyWaterDayCreate(day_id=uuid.uuid4()),
            VarietyWaterDayCreate(day_id=uuid.uuid4()),
        ]

        # Setup mocks
        uow.variety_repo.variety_name_exists_for_user.return_value = False
        created_variety = make_variety(user_id)
        mock_factory.create_variety.return_value = created_variety
        uow.variety_repo.create_variety.return_value = created_variety

        water_days = [AsyncMock(), AsyncMock()]
        mock_factory.create_water_days.return_value = water_days

        result = await uow.create_variety(variety_create_data, user_id)

        assert result == created_variety
        mock_factory.create_water_days.assert_called_once()
        uow.variety_repo.create_water_days.assert_called_once_with(water_days)
        mock_logger.info.assert_called()

    async def test_get_variety_success(self, uow, user_id, mocker):
        """Test successful variety retrieval."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        variety_id = uuid.uuid4()
        variety = make_variety(user_id)
        uow.variety_repo.get_variety_by_id.return_value = variety

        result = await uow.get_variety(variety_id, user_id)

        assert result == variety
        uow.variety_repo.get_variety_by_id.assert_called_once_with(variety_id, user_id)
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_get_variety", request_id=uow.request_id
        )

    async def test_get_variety_not_found(self, uow, user_id, mocker):
        """Test variety retrieval when variety doesn't exist."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        variety_id = uuid.uuid4()
        uow.variety_repo.get_variety_by_id.return_value = None

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await uow.get_variety(variety_id, user_id)

        # Check the exception message contains the expected information
        assert "variety" in str(exc_info.value.message)
        assert str(variety_id) in str(exc_info.value.message)
        mock_logger.info.assert_called_once()

    async def test_get_user_varieties(self, uow, user_id, mocker):
        """Test getting all user varieties."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        varieties = [make_variety(user_id), make_variety(user_id)]
        uow.variety_repo.get_user_varieties.return_value = varieties

        result = await uow.get_user_varieties(user_id)

        assert result == varieties
        uow.variety_repo.get_user_varieties.assert_called_once_with(user_id)
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_get_user_varieties", request_id=uow.request_id
        )

    async def test_get_public_varieties(self, uow, mocker):
        """Test getting all public varieties."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        varieties = [make_variety(uuid.uuid4(), is_public=True)]
        uow.variety_repo.get_public_varieties.return_value = varieties

        result = await uow.get_public_varieties()

        assert result == varieties
        uow.variety_repo.get_public_varieties.assert_called_once()
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_get_public_varieties", request_id=uow.request_id
        )

    async def test_update_variety_success(self, uow, user_id, mocker):
        """Test successful variety update."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        variety_id = uuid.uuid4()
        variety = make_variety(user_id, variety_name="Original Name")
        variety.owner_user_id = user_id  # Ensure ownership
        variety_data = VarietyUpdate(variety_name="Updated Name")

        uow.variety_repo.get_variety_by_id.return_value = variety
        uow.variety_repo.variety_name_exists_for_user.return_value = (
            False  # No conflict
        )
        updated_variety = make_variety(user_id, variety_name="Updated Name")
        mock_factory.update_variety.return_value = updated_variety
        uow.variety_repo.update_variety.return_value = updated_variety

        result = await uow.update_variety(variety_id, variety_data, user_id)

        assert result == updated_variety
        uow.variety_repo.get_variety_by_id.assert_called_once_with(variety_id, user_id)
        uow.variety_repo.variety_name_exists_for_user.assert_called_once_with(
            user_id, "Updated Name", exclude_variety_id=variety_id
        )
        mock_factory.update_variety.assert_called_once_with(variety, variety_data)
        uow.variety_repo.update_variety.assert_called_once_with(updated_variety)
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_update_variety", request_id=uow.request_id
        )

    async def test_update_variety_not_found(self, uow, user_id, mocker):
        """Test variety update when variety doesn't exist."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        variety_id = uuid.uuid4()
        variety_data = VarietyUpdate(variety_name="Updated Name")
        uow.variety_repo.get_variety_by_id.return_value = None

        with pytest.raises(ResourceNotFoundError):
            await uow.update_variety(variety_id, variety_data, user_id)

        mock_logger.info.assert_called_once()

    async def test_update_variety_wrong_owner(self, uow, user_id, mocker):
        """Test variety update fails when user doesn't own variety."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        variety_id = uuid.uuid4()
        variety = make_variety(uuid.uuid4())  # Different owner
        variety_data = VarietyUpdate(variety_name="Updated Name")
        uow.variety_repo.get_variety_by_id.return_value = variety

        with pytest.raises(BusinessLogicError) as exc_info:
            await uow.update_variety(variety_id, variety_data, user_id)

        assert exc_info.value.status_code == 403
        assert "only update your own" in str(exc_info.value.message)
        mock_logger.info.assert_called_once()

    async def test_update_variety_name_conflict(self, uow, user_id, mocker):
        """Test variety update fails when new name conflicts."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        variety_id = uuid.uuid4()
        variety = make_variety(user_id, variety_name="Original Name")
        variety.owner_user_id = user_id
        variety_data = VarietyUpdate(variety_name="Conflicting Name")

        uow.variety_repo.get_variety_by_id.return_value = variety
        uow.variety_repo.variety_name_exists_for_user.return_value = True

        with pytest.raises(BusinessLogicError) as exc_info:
            await uow.update_variety(variety_id, variety_data, user_id)

        assert exc_info.value.status_code == 409
        assert "already exists" in str(exc_info.value.message)
        mock_logger.info.assert_called_once()

    async def test_update_variety_with_water_days(self, uow, user_id, mocker):
        """Test variety update with water days modification."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        variety_id = uuid.uuid4()
        variety = make_variety(user_id)
        variety.owner_user_id = user_id

        from app.api.schemas.grow_guide.variety_schema import VarietyWaterDayCreate

        variety_data = VarietyUpdate(
            water_days=[VarietyWaterDayCreate(day_id=uuid.uuid4())]
        )

        uow.variety_repo.get_variety_by_id.return_value = variety
        updated_variety = make_variety(user_id)
        mock_factory.update_variety.return_value = updated_variety
        uow.variety_repo.update_variety.return_value = updated_variety

        water_days = [AsyncMock()]
        mock_factory.create_water_days.return_value = water_days

        result = await uow.update_variety(variety_id, variety_data, user_id)

        assert result == updated_variety
        uow.variety_repo.delete_water_days.assert_called_once_with(variety_id)
        mock_factory.create_water_days.assert_called_once()
        uow.variety_repo.create_water_days.assert_called_once_with(water_days)
        mock_logger.info.assert_called()

    async def test_delete_variety_success(self, uow, user_id, mocker):
        """Test successful variety deletion."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        mock_log_timing = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.log_timing"
        )

        variety_id = uuid.uuid4()
        uow.variety_repo.delete_variety.return_value = True

        result = await uow.delete_variety(variety_id, user_id)

        assert result is True
        uow.variety_repo.delete_variety.assert_called_once_with(variety_id, user_id)
        mock_logger.info.assert_called()
        mock_log_timing.assert_called_once_with(
            "uow_delete_variety", request_id=uow.request_id
        )

    async def test_delete_variety_not_found(self, uow, user_id, mocker):
        """Test variety deletion when variety doesn't exist."""
        mock_logger = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.logger"
        )
        variety_id = uuid.uuid4()
        uow.variety_repo.delete_variety.return_value = False

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await uow.delete_variety(variety_id, user_id)

        # Check the exception message contains the expected information
        assert "variety" in str(exc_info.value.message)
        assert str(variety_id) in str(exc_info.value.message)
        mock_logger.info.assert_called_once()


class TestGrowGuideUnitOfWorkInitialization:
    """Test the initialization and repository setup."""

    def test_initialization(self, mock_db, mocker):
        """Test that UoW initializes with all required repositories."""
        mock_request_id = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.request_id_ctx_var"
        )
        mock_request_id.get.return_value = "test-request-id"

        mock_day_repo = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.DayRepository"
        )
        mock_variety_repo = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyRepository"
        )
        mock_week_repo = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.WeekRepository"
        )
        mock_month_repo = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.MonthRepository"
        )
        mock_family_repo = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.FamilyRepository"
        )

        uow = GrowGuideUnitOfWork(mock_db)

        assert uow.db is mock_db
        assert uow.request_id == "test-request-id"
        mock_day_repo.assert_called_once_with(mock_db)
        mock_variety_repo.assert_called_once_with(mock_db)
        mock_week_repo.assert_called_once_with(mock_db)
        mock_month_repo.assert_called_once_with(mock_db)
        mock_family_repo.assert_called_once_with(mock_db)


class TestGrowGuideUnitOfWorkErrorHandling:
    """Test error handling and edge cases."""

    @pytest.fixture
    def uow(self, mock_db):
        """Create a GrowGuideUnitOfWork instance with mocked repositories."""
        uow = GrowGuideUnitOfWork(mock_db)
        uow.variety_repo = AsyncMock()
        return uow

    @pytest.fixture
    def user_id(self):
        """Sample user ID."""
        return uuid.uuid4()

    async def test_update_variety_with_empty_water_days_list(
        self, uow, user_id, mocker
    ):
        """Test variety update with empty water days list."""
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        variety_id = uuid.uuid4()
        variety = make_variety(user_id)
        variety.owner_user_id = user_id
        variety_data = VarietyUpdate(water_days=[])  # Empty list

        uow.variety_repo.get_variety_by_id.return_value = variety
        updated_variety = make_variety(user_id)
        mock_factory.update_variety.return_value = updated_variety
        uow.variety_repo.update_variety.return_value = updated_variety

        result = await uow.update_variety(variety_id, variety_data, user_id)

        assert result == updated_variety
        uow.variety_repo.delete_water_days.assert_called_once_with(variety_id)
        # Should not create new water days when list is empty
        mock_factory.create_water_days.assert_not_called()
        uow.variety_repo.create_water_days.assert_not_called()

    async def test_update_variety_no_name_change(self, uow, user_id, mocker):
        """Test variety update when name is not changed."""
        mock_factory = mocker.patch(
            "app.api.services.grow_guide.grow_guide_unit_of_work.VarietyFactory"
        )

        variety_id = uuid.uuid4()
        variety = make_variety(user_id, variety_name="Same Name")
        variety.owner_user_id = user_id
        variety_data = VarietyUpdate(variety_name="Same Name")  # Same name

        uow.variety_repo.get_variety_by_id.return_value = variety
        updated_variety = make_variety(user_id)
        mock_factory.update_variety.return_value = updated_variety
        uow.variety_repo.update_variety.return_value = updated_variety

        result = await uow.update_variety(variety_id, variety_data, user_id)

        assert result == updated_variety
        # Should not check for name conflicts when name hasn't changed
        uow.variety_repo.variety_name_exists_for_user.assert_not_called()
