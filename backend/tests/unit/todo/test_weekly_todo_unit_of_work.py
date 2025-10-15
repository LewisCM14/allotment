"""
Unit tests for WeeklyTodoUnitOfWork.
"""

import uuid
from unittest.mock import AsyncMock, MagicMock

import pytest

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.services.todo.weekly_todo import WeeklyTodoUnitOfWork


class TestWeeklyTodoUnitOfWork:
    @pytest.fixture
    def uow(self, mock_db):
        """Create a WeeklyTodoUnitOfWork instance with mocked dependencies."""
        instance = WeeklyTodoUnitOfWork(mock_db)
        instance.user_repo = AsyncMock()
        instance.week_repo = AsyncMock()
        instance.day_repo = AsyncMock()
        return instance

    @pytest.mark.asyncio
    async def test_aenter_returns_self(self, uow, mocker):
        """Test that __aenter__ returns self and logs correctly."""
        mock_logger = mocker.patch("app.api.services.todo.weekly_todo.logger")
        result = await uow.__aenter__()
        assert result is uow
        mock_logger.debug.assert_called_once_with(
            "Starting weekly todo unit of work",
            request_id=uow.request_id,
            transaction="begin",
        )

    @pytest.mark.asyncio
    async def test_aexit_commits_on_success(self, uow, mocker):
        """Test that __aexit__ commits on success."""
        mock_logger = mocker.patch("app.api.services.todo.weekly_todo.logger")
        mock_log_timing = mocker.patch("app.api.services.todo.weekly_todo.log_timing")
        await uow.__aexit__(None, None, None)
        uow.db.commit.assert_called_once()
        mock_log_timing.assert_called_once_with(
            "weekly_todo_commit", request_id=uow.request_id
        )
        mock_logger.debug.assert_called_with(
            "Transaction committed successfully",
            transaction="commit",
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_aexit_rolls_back_on_error(self, uow, mocker):
        """Test that __aexit__ rolls back on error."""
        mock_logger = mocker.patch("app.api.services.todo.weekly_todo.logger")
        await uow.__aexit__(ValueError, ValueError("boom"), None)
        uow.db.rollback.assert_called_once()
        mock_logger.warning.assert_called()
        mock_logger.debug.assert_called_with(
            "Transaction rolled back",
            request_id=uow.request_id,
        )

    @pytest.mark.asyncio
    async def test_parse_uuid_valid(self, uow):
        """Test _parse_uuid with valid UUID string."""
        test_uuid = uuid.uuid4()
        result = uow._parse_uuid(str(test_uuid), "test_field")
        assert result == test_uuid

    @pytest.mark.asyncio
    async def test_parse_uuid_invalid(self, uow):
        """Test _parse_uuid with invalid UUID string."""
        with pytest.raises(BusinessLogicError) as exc_info:
            uow._parse_uuid("not-a-uuid", "test_field")
        assert "Invalid test_field format" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_current_week_number(self, uow):
        """Test _get_current_week_number returns valid week number."""
        week_number = uow._get_current_week_number()
        assert 1 <= week_number <= 53  # ISO week can be 53 in some years

    @pytest.mark.asyncio
    async def test_get_week_by_number_success(self, uow, mocker):
        """Test _get_week_by_number returns week when found."""
        mock_week = MagicMock()
        mock_week.week_id = uuid.uuid4()
        mock_week.week_number = 20

        mock_scalars = MagicMock()
        mock_scalars.scalar_one_or_none.return_value = mock_week

        async def mock_execute(*args, **kwargs):
            return mock_scalars

        uow.db.execute = mock_execute

        result = await uow._get_week_by_number(20)
        assert result == mock_week

    @pytest.mark.asyncio
    async def test_get_week_by_number_not_found(self, uow, mocker):
        """Test _get_week_by_number returns None when week not found."""
        mock_scalars = MagicMock()
        mock_scalars.scalar_one_or_none.return_value = None

        async def mock_execute(*args, **kwargs):
            return mock_scalars

        uow.db.execute = mock_execute

        result = await uow._get_week_by_number(99)
        assert result is None

    @pytest.mark.asyncio
    async def test_get_weekly_todo_week_not_found(self, uow, mocker):
        """Test get_weekly_todo raises error when week not found."""
        user_id = str(uuid.uuid4())

        # Mock _get_week_by_number to return None
        mocker.patch.object(uow, "_get_week_by_number", return_value=None)
        mocker.patch.object(uow, "_get_current_week_number", return_value=20)

        with pytest.raises(ResourceNotFoundError) as exc_info:
            await uow.get_weekly_todo(user_id, week_number=20)
        assert "Week" in str(exc_info.value)

    @pytest.mark.asyncio
    async def test_get_weekly_todo_no_active_varieties(self, uow, mocker):
        """Test get_weekly_todo returns empty response when no active varieties."""
        user_id = str(uuid.uuid4())
        mock_week = MagicMock()
        mock_week.week_id = uuid.uuid4()
        mock_week.week_number = 20
        mock_week.week_start_date = "05/13"
        mock_week.week_end_date = "05/19"

        mocker.patch.object(uow, "_get_week_by_number", return_value=mock_week)
        mocker.patch.object(uow, "_get_current_week_number", return_value=20)
        mocker.patch.object(uow, "_get_user_active_varieties", return_value=[])
        mock_logger = mocker.patch("app.api.services.todo.weekly_todo.logger")

        result = await uow.get_weekly_todo(user_id, week_number=20)

        assert result["week_number"] == 20
        assert result["weekly_tasks"]["sow_tasks"] == []
        assert result["daily_tasks"] == {}
        mock_logger.info.assert_called()

    @pytest.mark.asyncio
    async def test_get_weekly_todo_with_active_varieties(self, uow, mocker):
        """Test get_weekly_todo returns tasks when user has active varieties."""
        user_id = str(uuid.uuid4())
        mock_week = MagicMock()
        mock_week.week_id = uuid.uuid4()
        mock_week.week_number = 20
        mock_week.week_start_date = "05/13"
        mock_week.week_end_date = "05/19"

        mock_variety = MagicMock()
        mock_variety.variety_id = uuid.uuid4()
        mock_variety.variety_name = "tomato"

        mock_weekly_tasks = {
            "sow_tasks": [
                {
                    "variety_id": mock_variety.variety_id,
                    "variety_name": "tomato",
                    "family_name": "nightshade",
                }
            ],
            "transplant_tasks": [],
            "harvest_tasks": [],
            "prune_tasks": [],
            "compost_tasks": [],
        }

        mock_daily_tasks = {
            1: {
                "day_id": uuid.uuid4(),
                "day_number": 1,
                "day_name": "Mon",
                "feed_tasks": [],
                "water_tasks": [],
            }
        }

        mocker.patch.object(uow, "_get_week_by_number", return_value=mock_week)
        mocker.patch.object(uow, "_get_current_week_number", return_value=20)
        mocker.patch.object(
            uow, "_get_user_active_varieties", return_value=[mock_variety]
        )
        mocker.patch.object(uow, "_build_weekly_tasks", return_value=mock_weekly_tasks)
        mocker.patch.object(uow, "_build_daily_tasks", return_value=mock_daily_tasks)

        result = await uow.get_weekly_todo(user_id, week_number=20)

        assert result["week_number"] == 20
        assert len(result["weekly_tasks"]["sow_tasks"]) == 1
        assert 1 in result["daily_tasks"]

    @pytest.mark.asyncio
    async def test_build_water_tasks_for_day(self, uow):
        """Test _build_water_tasks_for_day uses frequency default days."""
        day_id = uuid.uuid4()

        # Mock variety with water frequency that includes this day
        mock_variety_1 = MagicMock()
        mock_variety_1.variety_id = uuid.uuid4()
        mock_variety_1.variety_name = "lettuce"
        mock_variety_1.family.family_name = "asteraceae"
        mock_water_frequency = MagicMock()
        mock_default_day = MagicMock()
        mock_default_day.day_id = day_id
        mock_water_frequency.default_days = [mock_default_day]
        mock_variety_1.water_frequency = mock_water_frequency

        # Mock variety with water frequency that doesn't include this day
        mock_variety_2 = MagicMock()
        mock_variety_2.variety_id = uuid.uuid4()
        mock_variety_2.variety_name = "tomato"
        mock_water_frequency_2 = MagicMock()
        mock_other_day = MagicMock()
        mock_other_day.day_id = uuid.uuid4()  # Different day
        mock_water_frequency_2.default_days = [mock_other_day]
        mock_variety_2.water_frequency = mock_water_frequency_2

        result = uow._build_water_tasks_for_day(
            [mock_variety_1, mock_variety_2], day_id
        )

        assert len(result) == 1
        assert result[0]["variety_name"] == "lettuce"

    @pytest.mark.asyncio
    async def test_is_week_in_range_by_number(self, uow):
        """Test _is_week_in_range_by_number handles normal and wrap-around cases."""
        week_id_1 = uuid.uuid4()
        week_id_2 = uuid.uuid4()
        week_id_3 = uuid.uuid4()

        # Normal case: week 10 to week 20
        week_map = {week_id_1: 10, week_id_2: 20, week_id_3: 15}

        # Test within range
        result = await uow._is_week_in_range_by_number(
            15, week_id_1, week_id_2, week_map
        )
        assert result is True

        # Test at start
        result = await uow._is_week_in_range_by_number(
            10, week_id_1, week_id_2, week_map
        )
        assert result is True

        # Test at end
        result = await uow._is_week_in_range_by_number(
            20, week_id_1, week_id_2, week_map
        )
        assert result is True

        # Test outside range
        result = await uow._is_week_in_range_by_number(
            5, week_id_1, week_id_2, week_map
        )
        assert result is False

        # Wrap-around case: week 50 to week 5
        week_id_4 = uuid.uuid4()
        week_id_5 = uuid.uuid4()
        wrap_map = {week_id_4: 50, week_id_5: 5}

        # Test week 52 (in range)
        result = await uow._is_week_in_range_by_number(
            52, week_id_4, week_id_5, wrap_map
        )
        assert result is True

        # Test week 3 (in range)
        result = await uow._is_week_in_range_by_number(
            3, week_id_4, week_id_5, wrap_map
        )
        assert result is True

        # Test week 25 (out of range)
        result = await uow._is_week_in_range_by_number(
            25, week_id_4, week_id_5, wrap_map
        )
        assert result is False

    @pytest.mark.asyncio
    async def test_create_empty_todo_response(self, uow):
        """Test _create_empty_todo_response creates correct structure."""
        mock_week = MagicMock()
        mock_week.week_id = uuid.uuid4()
        mock_week.week_number = 15
        mock_week.week_start_date = "04/08"
        mock_week.week_end_date = "04/14"

        result = uow._create_empty_todo_response(mock_week)

        assert result["week_number"] == 15
        assert result["week_start_date"] == "04/08"
        assert result["weekly_tasks"]["sow_tasks"] == []
        assert result["daily_tasks"] == {}

    @pytest.mark.asyncio
    async def test_get_user_active_varieties(self, uow, mocker):
        """Test _get_user_active_varieties queries correctly."""
        user_id = uuid.uuid4()

        mock_variety = MagicMock()
        mock_variety.variety_id = uuid.uuid4()

        mock_scalars = MagicMock()
        mock_unique = MagicMock()
        mock_unique.all.return_value = [mock_variety]
        mock_scalars.unique.return_value = mock_unique

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args, **kwargs):
            return mock_result

        uow.db.execute = mock_execute

        result = await uow._get_user_active_varieties(user_id)

        assert len(result) == 1
        assert result[0] == mock_variety

    @pytest.mark.asyncio
    async def test_get_user_feed_days(self, uow, mocker):
        """Test _get_user_feed_days returns feed to day mapping."""
        user_id = uuid.uuid4()
        feed_id_1 = uuid.uuid4()
        feed_id_2 = uuid.uuid4()
        day_id_1 = uuid.uuid4()
        day_id_2 = uuid.uuid4()

        mock_user_feed_day_1 = MagicMock()
        mock_user_feed_day_1.feed_id = feed_id_1
        mock_user_feed_day_1.day_id = day_id_1

        mock_user_feed_day_2 = MagicMock()
        mock_user_feed_day_2.feed_id = feed_id_2
        mock_user_feed_day_2.day_id = day_id_2

        mock_scalars = MagicMock()
        mock_scalars.all.return_value = [mock_user_feed_day_1, mock_user_feed_day_2]

        mock_result = MagicMock()
        mock_result.scalars.return_value = mock_scalars

        async def mock_execute(*args, **kwargs):
            return mock_result

        uow.db.execute = mock_execute

        result = await uow._get_user_feed_days(user_id)

        assert result[feed_id_1] == day_id_1
        assert result[feed_id_2] == day_id_2
