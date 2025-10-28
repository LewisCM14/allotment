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
    async def test_aexit_rolls_back_on_unknown_error(self, uow, mocker):
        """Covers the path where exc_type is set but exc_value is None."""
        mock_logger = mocker.patch("app.api.services.todo.weekly_todo.logger")

        class SomeError(Exception):
            pass

        await uow.__aexit__(SomeError, None, None)
        uow.db.rollback.assert_called()
        # Ensure the 'unknown error' log path is used
        assert any(
            call.kwargs.get("error_type") == str(SomeError)
            for call in mock_logger.warning.call_args_list
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
    async def test_get_weekly_todo_uses_current_week_when_none(self, uow, mocker):
        """When week_number is None, it should use _get_current_week_number()."""
        user_id = str(uuid.uuid4())
        mock_week = MagicMock()
        mock_week.week_id = uuid.uuid4()
        mock_week.week_number = 42
        mock_week.week_start_date = "10/09"
        mock_week.week_end_date = "10/15"

        mocker.patch.object(uow, "_get_current_week_number", return_value=42)
        mocker.patch.object(uow, "_get_week_by_number", return_value=mock_week)
        mocker.patch.object(uow, "_get_user_active_varieties", return_value=[])

        result = await uow.get_weekly_todo(user_id, week_number=None)
        assert result["week_number"] == 42

    @pytest.mark.asyncio
    async def test_build_water_tasks_for_day(self, uow):
        """Test _build_water_tasks_for_day uses frequency default days."""
        day_id = uuid.uuid4()

        # Mock variety with water frequency that includes this day
        mock_variety_1 = MagicMock()
        mock_variety_1.variety_id = uuid.uuid4()
        mock_variety_1.variety_name = "lettuce"
        mock_variety_1.family.family_name = "asteraceae"
        # Ensure non-annual to avoid DB fallback path for missing week numbers
        mock_variety_1.lifecycle.lifecycle_name = "perennial"
        mock_water_frequency = MagicMock()
        mock_default_day = MagicMock()
        mock_default_day.day_id = day_id
        mock_water_frequency.default_days = [mock_default_day]
        mock_variety_1.water_frequency = mock_water_frequency

        # Mock variety with water frequency that doesn't include this day
        mock_variety_2 = MagicMock()
        mock_variety_2.variety_id = uuid.uuid4()
        mock_variety_2.variety_name = "tomato"
        mock_variety_2.lifecycle.lifecycle_name = "perennial"
        mock_water_frequency_2 = MagicMock()
        mock_other_day = MagicMock()
        mock_other_day.day_id = uuid.uuid4()  # Different day
        mock_water_frequency_2.default_days = [mock_other_day]
        mock_variety_2.water_frequency = mock_water_frequency_2

        result = await uow._build_water_tasks_for_day(
            [mock_variety_1, mock_variety_2],
            day_id,
            week_number=10,
            week_id_to_number={},
        )

        assert len(result) == 1
        assert result[0]["variety_name"] == "lettuce"

    @pytest.mark.asyncio
    async def test_to_lifecycle_type_and_compost_logic(self, uow):
        """Cover _to_lifecycle_type and _should_compost_variety annual logic including wrap-around."""
        from app.api.models.enums import LifecycleType

        # _to_lifecycle_type accepts strings and enums, defaults to ANNUAL
        assert uow._to_lifecycle_type("ANNUAL") == LifecycleType.ANNUAL
        assert (
            uow._to_lifecycle_type("short-lived perennial")
            == LifecycleType.SHORT_LIVED_PERENNIAL
        )
        assert (
            uow._to_lifecycle_type(LifecycleType.PERENNIAL) == LifecycleType.PERENNIAL
        )
        assert uow._to_lifecycle_type("UnknownKind") == LifecycleType.ANNUAL

        # Compost logic for annuals: non-wrap season -> compost strictly after harvest_end
        sow_id, harvest_id = uuid.uuid4(), uuid.uuid4()
        week_map = {sow_id: 8, harvest_id: 30}
        annual = MagicMock()
        annual.lifecycle.lifecycle_name = "annual"
        annual.sow_week_start_id = sow_id
        annual.harvest_week_end_id = harvest_id
        assert await uow._should_compost_variety(annual, 31, week_map) is True
        assert await uow._should_compost_variety(annual, 5, week_map) is False

        # Wrap-around season (e.g., sow 50 .. harvest 10) -> compost between harvest_end and next sow_start
        sow2, harvest2 = uuid.uuid4(), uuid.uuid4()
        week_map2 = {sow2: 50, harvest2: 10}
        annual2 = MagicMock()
        annual2.lifecycle.lifecycle_name = "annual"
        annual2.sow_week_start_id = sow2
        annual2.harvest_week_end_id = harvest2
        assert await uow._should_compost_variety(annual2, 11, week_map2) is True
        assert await uow._should_compost_variety(annual2, 9, week_map2) is False

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

    @pytest.mark.asyncio
    async def test_is_week_in_range_missing_numbers_returns_false(self, uow):
        """If either start or end week number missing in map, result is False."""
        week_map = {}
        res = await uow._is_week_in_range_by_number(
            10, uuid.uuid4(), uuid.uuid4(), week_map
        )
        assert res is False

    @pytest.mark.asyncio
    async def test_build_weekly_tasks_handles_none_week(self, uow, mocker):
        """If _get_week_by_id returns None, returns empty tasks structure."""
        mocker.patch.object(uow, "_get_week_by_id", return_value=None)
        tasks = await uow._build_weekly_tasks([], uuid.uuid4())
        assert tasks == {
            "sow_tasks": [],
            "transplant_tasks": [],
            "harvest_tasks": [],
            "prune_tasks": [],
            "compost_tasks": [],
        }

    @pytest.mark.asyncio
    async def test_build_weekly_tasks_transplant_and_prune(self, uow, mocker):
        """Covers transplant and prune additions when in range."""
        # Current week
        mock_current_week = MagicMock()
        mock_current_week.week_number = 15
        mocker.patch.object(uow, "_get_week_by_id", return_value=mock_current_week)

        # Week map so all ranges include week 15
        mocker.patch.object(
            uow, "_get_week_id_to_number_map", return_value={uuid.uuid4(): 10}
        )

        # Shortcut range checks to True for specific calls
        async def range_true(*args, **kwargs):
            return True

        mocker.patch.object(uow, "_is_week_in_range_by_number", side_effect=range_true)

        variety = MagicMock()
        variety.variety_id = uuid.uuid4()
        variety.variety_name = "pepper"
        variety.family.family_name = "nightshade"
        # Needed ids (values only used by mocked range fn)
        variety.sow_week_start_id = uuid.uuid4()
        variety.sow_week_end_id = uuid.uuid4()
        variety.harvest_week_start_id = uuid.uuid4()
        variety.harvest_week_end_id = uuid.uuid4()
        variety.transplant_week_start_id = uuid.uuid4()
        variety.transplant_week_end_id = uuid.uuid4()
        variety.prune_week_start_id = uuid.uuid4()
        variety.prune_week_end_id = uuid.uuid4()
        # Compost path
        mocker.patch.object(uow, "_should_compost_variety", return_value=True)

        res = await uow._build_weekly_tasks([variety], uuid.uuid4())
        assert {"variety_name": "pepper", "family_name": "nightshade"}.items() <= res[
            "sow_tasks"
        ][0].items()
        assert len(res["transplant_tasks"]) == 1
        assert len(res["prune_tasks"]) == 1
        assert len(res["harvest_tasks"]) == 1
        assert len(res["compost_tasks"]) == 1

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

    @pytest.mark.asyncio
    async def test_build_feed_tasks_for_day_grouping_and_default_lifecycle(
        self, uow, mocker
    ):
        """Two varieties with same feed_id should group; one has no lifecycle to hit default ANNUAL path."""
        day_id = uuid.uuid4()
        feed_id = uuid.uuid4()
        user_feed_days = {feed_id: day_id}

        v1 = MagicMock()
        v1.variety_id = uuid.uuid4()
        v1.variety_name = "a"
        v1.family.family_name = "fam"
        v1.feed_id = feed_id
        v1.feed = MagicMock()
        v1.feed.feed_name = "Tomato Feed"
        v1.feed_week_start_id = uuid.uuid4()
        v1.feed_frequency_id = uuid.uuid4()
        v1.harvest_week_end_id = uuid.uuid4()
        v1.lifecycle = None  # hits default to ANNUAL

        v2 = MagicMock()
        v2.variety_id = uuid.uuid4()
        v2.variety_name = "b"
        v2.family.family_name = "fam"
        v2.feed_id = feed_id
        v2.feed = v1.feed
        v2.feed_week_start_id = uuid.uuid4()
        v2.feed_frequency_id = uuid.uuid4()
        v2.harvest_week_end_id = uuid.uuid4()
        v2.lifecycle.lifecycle_name = "annual"

        # Force feeding period true for both
        mocker.patch.object(uow, "_is_week_in_feeding_period", return_value=True)

        res = await uow._build_feed_tasks_for_day([v1, v2], day_id, 12, user_feed_days)
        assert len(res) == 1
        assert res[0]["feed_id"] == feed_id
        assert res[0]["feed_name"] == "Tomato Feed"
        assert sorted([x["variety_name"] for x in res[0]["varieties"]]) == ["a", "b"]

    @pytest.mark.asyncio
    async def test_get_week_id_to_number_map(self, uow, mocker):
        """Ensure we collect all referenced weeks and return a map from DB query."""
        v = MagicMock()
        # Supply required week ids
        v.sow_week_start_id = uuid.uuid4()
        v.sow_week_end_id = uuid.uuid4()
        v.harvest_week_start_id = uuid.uuid4()
        v.harvest_week_end_id = uuid.uuid4()
        v.transplant_week_start_id = uuid.uuid4()
        v.transplant_week_end_id = uuid.uuid4()
        v.prune_week_start_id = uuid.uuid4()
        v.prune_week_end_id = uuid.uuid4()
        v.feed_week_start_id = uuid.uuid4()

        pairs = [
            (v.sow_week_start_id, 5),
            (v.sow_week_end_id, 10),
            (v.harvest_week_start_id, 20),
            (v.harvest_week_end_id, 30),
            (v.transplant_week_start_id, 12),
            (v.transplant_week_end_id, 14),
            (v.prune_week_start_id, 25),
            (v.prune_week_end_id, 27),
            (v.feed_week_start_id, 8),
        ]

        mock_result = MagicMock()
        mock_result.all.return_value = pairs
        uow.db.execute = AsyncMock(return_value=mock_result)

        mapping = await uow._get_week_id_to_number_map([v])
        for k, n in pairs:
            assert mapping[k] == n

    @pytest.mark.asyncio
    async def test_build_water_tasks_fallback_fetch(self, uow):
        """Annual variety triggers fallback fetch of missing week numbers and is added when in-season and day matches."""
        sow_id, harv_id, day_id = uuid.uuid4(), uuid.uuid4(), uuid.uuid4()

        v = MagicMock()
        v.variety_id = uuid.uuid4()
        v.variety_name = "cucumber"
        v.family.family_name = "cucurbit"
        v.lifecycle.lifecycle_name = "annual"
        v.sow_week_start_id = sow_id
        v.harvest_week_end_id = harv_id
        wf = MagicMock()
        d = MagicMock()
        d.day_id = day_id
        wf.default_days = [d]
        v.water_frequency = wf

        # DB returns both week numbers in one call
        pairs = [(sow_id, 8), (harv_id, 30)]
        mock_result = MagicMock()
        mock_result.all.return_value = pairs
        uow.db.execute = AsyncMock(return_value=mock_result)

        res = await uow._build_water_tasks_for_day([v], day_id, 10, {})
        assert len(res) == 1 and res[0]["variety_name"] == "cucumber"

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


# Lightweight, module-scoped feeding-period variants test
@pytest.mark.asyncio
async def test_is_week_in_feeding_period_variants():
    """Exercise weekly/monthly/yearly cadence and perennial path including wrap-around handling using standard AsyncMock sessions."""
    from types import SimpleNamespace

    from sqlalchemy.ext.asyncio import AsyncSession

    def scalar_result(value):
        r = MagicMock()
        r.scalar_one_or_none.return_value = value
        return r

    start_week = 10
    harvest_end = 30

    # Weekly cadence: every week from start within annual window
    weekly_freq = SimpleNamespace(frequency_days_per_year=52)
    db1 = AsyncMock(spec=AsyncSession)
    db1.execute.side_effect = [
        scalar_result(start_week),  # feed start
        scalar_result(harvest_end),  # harvest end
        scalar_result(weekly_freq),  # frequency
    ]
    uow1 = WeeklyTodoUnitOfWork(db1)
    assert (
        await uow1._is_week_in_feeding_period(
            week_number=12,
            feed_week_start_id=uuid.uuid4(),
            feed_frequency_id=uuid.uuid4(),
            harvest_week_end_id=uuid.uuid4(),
            lifecycle_name="annual",
        )
        is True
    )

    # Monthly-ish cadence (~every 4 weeks)
    monthly_freq = SimpleNamespace(frequency_days_per_year=12)
    db2 = AsyncMock(spec=AsyncSession)
    db2.execute.side_effect = [
        scalar_result(start_week),
        scalar_result(harvest_end),
        scalar_result(monthly_freq),
    ]
    uow2 = WeeklyTodoUnitOfWork(db2)
    # Exactly 4 weeks since start feeds
    assert (
        await uow2._is_week_in_feeding_period(
            week_number=14,
            feed_week_start_id=uuid.uuid4(),
            feed_frequency_id=uuid.uuid4(),
            harvest_week_end_id=uuid.uuid4(),
            lifecycle_name="annual",
        )
        is True
    )

    # 3 weeks since start does not feed
    db3 = AsyncMock(spec=AsyncSession)
    db3.execute.side_effect = [
        scalar_result(start_week),
        scalar_result(harvest_end),
        scalar_result(monthly_freq),
    ]
    uow3 = WeeklyTodoUnitOfWork(db3)
    assert (
        await uow3._is_week_in_feeding_period(
            week_number=13,
            feed_week_start_id=uuid.uuid4(),
            feed_frequency_id=uuid.uuid4(),
            harvest_week_end_id=uuid.uuid4(),
            lifecycle_name="annual",
        )
        is False
    )

    # Perennial path where week < start_week is handled by adding 52 before cadence calculation
    yearly_freq = SimpleNamespace(frequency_days_per_year=1)
    db4 = AsyncMock(spec=AsyncSession)
    db4.execute.side_effect = [
        scalar_result(start_week),
        scalar_result(yearly_freq),  # frequency; no harvest query for perennials path
    ]
    uow4 = WeeklyTodoUnitOfWork(db4)
    assert (
        await uow4._is_week_in_feeding_period(
            week_number=5,  # < start -> adjusted by +52 internally
            feed_week_start_id=uuid.uuid4(),
            feed_frequency_id=uuid.uuid4(),
            harvest_week_end_id=uuid.uuid4(),
            lifecycle_name="perennial",
        )
        is False
    )


@pytest.mark.asyncio
async def test_is_week_in_feeding_period_edge_cases():
    """Covers start week missing, frequency missing, and <=0 occurrences cases."""
    from types import SimpleNamespace

    from sqlalchemy.ext.asyncio import AsyncSession

    def scalar_result(value):
        r = MagicMock()
        r.scalar_one_or_none.return_value = value
        return r

    # Case 1: start week missing -> False
    db1 = AsyncMock(spec=AsyncSession)
    db1.execute.side_effect = [scalar_result(None)]
    uow1 = WeeklyTodoUnitOfWork(db1)
    assert (
        await uow1._is_week_in_feeding_period(
            10, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "annual"
        )
        is False
    )

    # Case 2: frequency row missing -> False
    start_week = 8
    harvest_end = 20
    db2 = AsyncMock(spec=AsyncSession)
    db2.execute.side_effect = [
        scalar_result(start_week),
        scalar_result(harvest_end),
        scalar_result(None),
    ]
    uow2 = WeeklyTodoUnitOfWork(db2)
    assert (
        await uow2._is_week_in_feeding_period(
            12, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "annual"
        )
        is False
    )

    # Case 3: occurrences_per_year <= 0 -> False
    zero_freq = SimpleNamespace(frequency_days_per_year=0)
    db3 = AsyncMock(spec=AsyncSession)
    db3.execute.side_effect = [
        scalar_result(start_week),
        scalar_result(harvest_end),
        scalar_result(zero_freq),
    ]
    uow3 = WeeklyTodoUnitOfWork(db3)
    assert (
        await uow3._is_week_in_feeding_period(
            12, uuid.uuid4(), uuid.uuid4(), uuid.uuid4(), "annual"
        )
        is False
    )
