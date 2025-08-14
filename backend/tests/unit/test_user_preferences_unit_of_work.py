import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.models.grow_guide.calendar_model import Day
from app.api.models.grow_guide.guide_options_model import Feed
from app.api.models.user.user_model import UserFeedDay
from app.api.repositories.grow_guide.day_repository import DayRepository
from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_preference_schema import (
    DayRead,
    FeedDayRead,
    FeedRead,
    UserPreferencesRead,
)
from app.api.services.user.user_preferences_unit_of_work import (
    UserPreferencesUnitOfWork,
)


class TestUserPreferencesUnitOfWork:
    """Test suite for UserPreferencesUnitOfWork."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def user_preferences_uow(self, mock_db):
        """Create a UserPreferencesUnitOfWork instance with mock database."""
        return UserPreferencesUnitOfWork(db=mock_db)

    @pytest.fixture
    def sample_user_feed_day(self):
        """Create a sample user feed day."""
        user_feed_day = MagicMock(spec=UserFeedDay)
        user_feed_day.feed_id = uuid.uuid4()
        user_feed_day.day_id = uuid.uuid4()

        # Mock the relationships
        user_feed_day.feed = MagicMock(spec=Feed)
        user_feed_day.feed.name = "Tomato Feed"
        user_feed_day.feed.id = user_feed_day.feed_id

        user_feed_day.day = MagicMock(spec=Day)
        user_feed_day.day.name = "Monday"
        user_feed_day.day.id = user_feed_day.day_id
        user_feed_day.day.day_number = 1

        return user_feed_day

    @pytest.fixture
    def sample_feeds(self):
        """Create sample feeds."""
        feeds = []
        for i, name in enumerate(["Tomato Feed", "General Feed", "Organic Compost"]):
            feed = MagicMock(spec=Feed)
            feed.id = uuid.uuid4()
            feed.name = name
            feeds.append(feed)
        return feeds

    @pytest.fixture
    def sample_days(self):
        """Create sample days."""
        days = []
        day_names = [
            "Monday",
            "Tuesday",
            "Wednesday",
            "Thursday",
            "Friday",
            "Saturday",
            "Sunday",
        ]
        for i, name in enumerate(day_names):
            day = MagicMock(spec=Day)
            day.id = uuid.uuid4()
            day.name = name
            day.day_number = i + 1
            days.append(day)
        return days

    def test_init(self, mock_db):
        """Test unit of work initialization."""
        uow = UserPreferencesUnitOfWork(db=mock_db)
        assert uow.db == mock_db
        assert isinstance(uow.user_repo, UserRepository)
        assert isinstance(uow.variety_repo, VarietyRepository)
        assert isinstance(uow.day_repo, DayRepository)

    @pytest.mark.asyncio
    async def test_context_manager_success(self, mock_db):
        """Test context manager successful transaction."""
        uow = UserPreferencesUnitOfWork(db=mock_db)

        async with uow:
            # Mock some operation
            pass

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, mock_db):
        """Test context manager with exception triggers rollback."""
        uow = UserPreferencesUnitOfWork(db=mock_db)

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test exception")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_exception_without_value(self, mock_db):
        """Test context manager with exception that has no value."""
        uow = UserPreferencesUnitOfWork(db=mock_db)

        # Create an exception without a message
        class TestException(Exception):
            def __str__(self):
                return ""

        with pytest.raises(TestException):
            async with uow:
                raise TestException()

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_integrity_error_on_commit(self, mock_db):
        """Test context manager handles IntegrityError during commit."""
        mock_db.commit.side_effect = IntegrityError("test", "test", "test")
        uow = UserPreferencesUnitOfWork(db=mock_db)

        with pytest.raises(IntegrityError):
            async with uow:
                pass

        mock_db.rollback.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_preferences_success(
        self, user_preferences_uow, sample_user_feed_day, sample_feeds, sample_days
    ):
        """Test successful retrieval of user preferences."""
        user_id = str(uuid.uuid4())
        user_feed_days = [sample_user_feed_day]

        with (
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
            patch.object(
                user_preferences_uow.variety_repo,
                "get_all_feeds",
                return_value=sample_feeds,
            ) as mock_get_feeds,
            patch.object(
                user_preferences_uow.day_repo, "get_all_days", return_value=sample_days
            ) as mock_get_days,
        ):
            result = await user_preferences_uow.get_user_preferences(user_id)

        assert isinstance(result, UserPreferencesRead)
        assert len(result.user_feed_days) == 1
        assert len(result.available_feeds) == 3
        assert len(result.available_days) == 7

        mock_get_feed_days.assert_called_once_with(user_id)
        mock_get_feeds.assert_called_once()
        mock_get_days.assert_called_once()

        # Check the structure of returned data
        feed_day = result.user_feed_days[0]
        assert isinstance(feed_day, FeedDayRead)
        assert feed_day.feed_id == sample_user_feed_day.feed_id
        assert feed_day.feed_name == sample_user_feed_day.feed.name
        assert feed_day.day_id == sample_user_feed_day.day_id
        assert feed_day.day_name == sample_user_feed_day.day.name

    @pytest.mark.asyncio
    async def test_get_user_preferences_empty_results(
        self, user_preferences_uow, sample_feeds, sample_days
    ):
        """Test user preferences retrieval with empty user feed days."""
        user_id = str(uuid.uuid4())
        user_feed_days = []

        with (
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
            patch.object(
                user_preferences_uow.variety_repo,
                "get_all_feeds",
                return_value=sample_feeds,
            ) as mock_get_feeds,
            patch.object(
                user_preferences_uow.day_repo, "get_all_days", return_value=sample_days
            ) as mock_get_days,
        ):
            result = await user_preferences_uow.get_user_preferences(user_id)

        assert isinstance(result, UserPreferencesRead)
        assert len(result.user_feed_days) == 0
        assert len(result.available_feeds) == 3
        assert len(result.available_days) == 7

        mock_get_feed_days.assert_called_once_with(user_id)
        mock_get_feeds.assert_called_once()
        mock_get_days.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_success(
        self, user_preferences_uow, sample_user_feed_day
    ):
        """Test successful update of user feed preference."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        # Update the sample to match the test parameters
        sample_user_feed_day.feed_id = uuid.UUID(feed_id)
        sample_user_feed_day.day_id = uuid.UUID(day_id)
        user_feed_days = [sample_user_feed_day]

        with (
            patch.object(
                user_preferences_uow.user_repo, "update_user_feed_day"
            ) as mock_update,
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
        ):
            result = await user_preferences_uow.update_user_feed_preference(
                user_id, feed_id, day_id
            )

        assert isinstance(result, FeedDayRead)
        assert str(result.feed_id) == feed_id
        assert str(result.day_id) == day_id
        assert result.feed_name == sample_user_feed_day.feed.name
        assert result.day_name == sample_user_feed_day.day.name

        mock_update.assert_called_once_with(user_id, feed_id, day_id)
        mock_get_feed_days.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_invalid_feed_id(
        self, user_preferences_uow
    ):
        """Test update with invalid feed_id format."""
        user_id = str(uuid.uuid4())
        feed_id = "invalid-uuid"
        day_id = str(uuid.uuid4())

        with pytest.raises(BusinessLogicError, match="Invalid feed_id format"):
            await user_preferences_uow.update_user_feed_preference(
                user_id, feed_id, day_id
            )

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_not_found_after_update(
        self, user_preferences_uow
    ):
        """Test update when preference is not found after update."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        # Return empty list after update (preference not found)
        user_feed_days = []

        with (
            patch.object(
                user_preferences_uow.user_repo, "update_user_feed_day"
            ) as mock_update,
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
        ):
            with pytest.raises(ResourceNotFoundError, match="Feed preference"):
                await user_preferences_uow.update_user_feed_preference(
                    user_id, feed_id, day_id
                )

        mock_update.assert_called_once_with(user_id, feed_id, day_id)
        mock_get_feed_days.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_different_ids_returned(
        self, user_preferences_uow, sample_user_feed_day
    ):
        """Test update when returned preference has different IDs."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        # Return a preference with different IDs
        sample_user_feed_day.feed_id = uuid.uuid4()  # Different from feed_id
        sample_user_feed_day.day_id = uuid.uuid4()  # Different from day_id
        user_feed_days = [sample_user_feed_day]

        with (
            patch.object(
                user_preferences_uow.user_repo, "update_user_feed_day"
            ) as mock_update,
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
        ):
            with pytest.raises(ResourceNotFoundError, match="Feed preference"):
                await user_preferences_uow.update_user_feed_preference(
                    user_id, feed_id, day_id
                )

        mock_update.assert_called_once_with(user_id, feed_id, day_id)
        mock_get_feed_days.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_multiple_matches(
        self, user_preferences_uow
    ):
        """Test update when multiple preferences match the IDs."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        # Create two matching preferences
        user_feed_day1 = MagicMock(spec=UserFeedDay)
        user_feed_day1.feed_id = uuid.UUID(feed_id)
        user_feed_day1.day_id = uuid.UUID(day_id)
        user_feed_day1.feed = MagicMock(spec=Feed)
        user_feed_day1.feed.name = "Feed 1"
        user_feed_day1.day = MagicMock(spec=Day)
        user_feed_day1.day.name = "Day 1"

        user_feed_day2 = MagicMock(spec=UserFeedDay)
        user_feed_day2.feed_id = uuid.UUID(feed_id)
        user_feed_day2.day_id = uuid.UUID(day_id)
        user_feed_day2.feed = MagicMock(spec=Feed)
        user_feed_day2.feed.name = "Feed 2"
        user_feed_day2.day = MagicMock(spec=Day)
        user_feed_day2.day.name = "Day 2"

        user_feed_days = [user_feed_day1, user_feed_day2]

        with (
            patch.object(
                user_preferences_uow.user_repo, "update_user_feed_day"
            ) as mock_update,
            patch.object(
                user_preferences_uow.user_repo,
                "get_user_feed_days",
                return_value=user_feed_days,
            ) as mock_get_feed_days,
        ):
            result = await user_preferences_uow.update_user_feed_preference(
                user_id, feed_id, day_id
            )

        # Should return the first match
        assert isinstance(result, FeedDayRead)
        assert str(result.feed_id) == feed_id
        assert str(result.day_id) == day_id
        assert result.feed_name == "Feed 1"
        assert result.day_name == "Day 1"

        mock_update.assert_called_once_with(user_id, feed_id, day_id)
        mock_get_feed_days.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_get_user_preferences_exception_handling(self, user_preferences_uow):
        """Test exception handling during get_user_preferences."""
        user_id = str(uuid.uuid4())

        with patch.object(
            user_preferences_uow.user_repo,
            "get_user_feed_days",
            side_effect=Exception("Database error"),
        ):
            with pytest.raises(Exception, match="Database error"):
                await user_preferences_uow.get_user_preferences(user_id)

    @pytest.mark.asyncio
    async def test_update_user_feed_preference_repo_exception(
        self, user_preferences_uow
    ):
        """Test exception handling during update_user_feed_preference."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        with patch.object(
            user_preferences_uow.user_repo,
            "update_user_feed_day",
            side_effect=Exception("Update failed"),
        ):
            with pytest.raises(Exception, match="Update failed"):
                await user_preferences_uow.update_user_feed_preference(
                    user_id, feed_id, day_id
                )

    @pytest.mark.asyncio
    async def test_feed_read_schema_creation(self, sample_feeds):
        """Test FeedRead schema creation from feed objects."""
        feeds = sample_feeds
        feed_reads = [FeedRead(id=feed.id, name=feed.name) for feed in feeds]

        assert len(feed_reads) == 3
        for i, feed_read in enumerate(feed_reads):
            assert isinstance(feed_read, FeedRead)
            assert feed_read.id == feeds[i].id
            assert feed_read.name == feeds[i].name

    @pytest.mark.asyncio
    async def test_day_read_schema_creation(self, sample_days):
        """Test DayRead schema creation from day objects."""
        days = sample_days
        day_reads = [
            DayRead(id=day.id, day_number=day.day_number, name=day.name) for day in days
        ]

        assert len(day_reads) == 7
        for i, day_read in enumerate(day_reads):
            assert isinstance(day_read, DayRead)
            assert day_read.id == days[i].id
            assert day_read.day_number == days[i].day_number
            assert day_read.name == days[i].name
