import uuid
from unittest.mock import MagicMock, Mock

import pytest
from fastapi import HTTPException, status

from app.api.middleware.exception_handler import InvalidTokenError
from app.api.models.user.user_model import (
    User,
    UserActiveVariety,
    UserAllotment,
    UserFeedDay,
)
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_allotment_schema import (
    UserAllotmentCreate,
    UserAllotmentUpdate,
)


class TestUserRepository:
    """Test suite for UserRepository (fixtures centralized in unit/user/conftest.py)."""

    def test_init(self, mock_db):
        """Test repository initialization."""
        repo = UserRepository(db=mock_db)
        assert repo.db == mock_db

    @pytest.mark.asyncio
    async def test_create_user(self, user_repository, mock_db, sample_user):
        """Test creating a new user."""
        result = await user_repository.create_user(sample_user)

        assert result == sample_user
        mock_db.add.assert_called_once_with(sample_user)

    # (Datetime-specific creation covered implicitly by model defaults; explicit test removed as redundant.)

    @pytest.mark.asyncio
    @pytest.mark.parametrize("already_verified", [False, True])
    async def test_verify_email_paths(
        self, user_repository, mock_db, sample_user, already_verified
    ):
        user_id = str(sample_user.user_id)
        sample_user.is_email_verified = already_verified
        mock_db.get.return_value = sample_user

        result = await user_repository.verify_email(user_id)

        assert result is sample_user
        assert sample_user.is_email_verified is True
        mock_db.get.assert_called_once_with(User, sample_user.user_id)
        if already_verified:
            mock_db.flush.assert_not_called()
        else:
            mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_verify_email_invalid_uuid(self, user_repository, mock_db):
        with pytest.raises(InvalidTokenError, match="Invalid user ID format"):
            await user_repository.verify_email("invalid-uuid")
        mock_db.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_verify_email_user_not_found(self, user_repository, mock_db):
        """Test email verification when user is not found."""
        user_id = str(uuid.uuid4())

        mock_db.get.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            await user_repository.verify_email(user_id)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "User not found"

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_repository, mock_db, sample_user):
        """Test getting user by email."""
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_user
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_user_by_email(sample_user.user_email)

        assert result == sample_user
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_repository, mock_db):
        """Test getting user by email when not found."""
        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_user_by_email("nonexistent@example.com")

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_password_success(
        self, user_repository, mock_db, sample_user
    ):
        user_id = str(sample_user.user_id)
        mock_db.get.return_value = sample_user
        result = await user_repository.update_user_password(user_id, "new_password")
        assert result is sample_user
        mock_db.get.assert_called_once_with(User, sample_user.user_id)

    @pytest.mark.asyncio
    async def test_update_user_password_invalid_uuid(self, user_repository, mock_db):
        with pytest.raises(InvalidTokenError, match="Invalid user ID format"):
            await user_repository.update_user_password("invalid-uuid", "new_password")
        mock_db.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_update_user_password_user_not_found(self, user_repository, mock_db):
        mock_db.get.return_value = None
        with pytest.raises(InvalidTokenError, match="User not found"):
            await user_repository.update_user_password(
                str(uuid.uuid4()), "new_password"
            )

    @pytest.mark.asyncio
    async def test_create_user_allotment(self, user_repository, mock_db):
        """Test creating a user allotment."""
        user_id = str(uuid.uuid4())
        allotment_data = UserAllotmentCreate(
            allotment_postal_zip_code="12345",
            allotment_width_meters=10.0,
            allotment_length_meters=10.0,
        )

        result = await user_repository.create_user_allotment(user_id, allotment_data)

        assert isinstance(result, UserAllotment)
        assert result.user_id == user_id
        assert (
            result.allotment_postal_zip_code == allotment_data.allotment_postal_zip_code
        )
        assert result.allotment_width_meters == allotment_data.allotment_width_meters
        assert result.allotment_length_meters == allotment_data.allotment_length_meters
        mock_db.add.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_allotment(self, user_repository, mock_db, sample_allotment):
        """Test getting user allotment."""
        user_id = str(sample_allotment.user_id)

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_allotment
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_user_allotment(user_id)

        assert result == sample_allotment
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_user_allotment_not_found(self, user_repository, mock_db):
        """Test getting user allotment when not found."""
        user_id = str(uuid.uuid4())

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_user_allotment(user_id)

        assert result is None
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_allotment_success(
        self, user_repository, mock_db, sample_allotment
    ):
        """Test updating a user allotment."""
        user_id = str(sample_allotment.user_id)
        update_data = UserAllotmentUpdate(
            allotment_postal_zip_code="54321",
            allotment_width_meters=15.0,
            allotment_length_meters=15.0,
        )

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = sample_allotment
        mock_db.execute.return_value = mock_result

        result = await user_repository.update_user_allotment(user_id, update_data)

        assert result == sample_allotment
        assert (
            sample_allotment.allotment_postal_zip_code
            == update_data.allotment_postal_zip_code
        )
        assert (
            sample_allotment.allotment_width_meters
            == update_data.allotment_width_meters
        )
        assert (
            sample_allotment.allotment_length_meters
            == update_data.allotment_length_meters
        )
        mock_db.add.assert_called_once_with(sample_allotment)

    @pytest.mark.asyncio
    async def test_update_user_allotment_not_found(self, user_repository, mock_db):
        """Test updating a user allotment that doesn't exist."""
        user_id = str(uuid.uuid4())
        update_data = UserAllotmentUpdate(allotment_postal_zip_code="54321")

        # Mock the query result
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        with pytest.raises(HTTPException) as exc_info:
            await user_repository.update_user_allotment(user_id, update_data)

        assert exc_info.value.status_code == status.HTTP_404_NOT_FOUND
        assert exc_info.value.detail == "Allotment not found"

    # User Preference Tests

    @pytest.mark.asyncio
    async def test_get_user_feed_days(
        self, user_repository, mock_db, sample_user_feed_day
    ):
        """Test getting user feed day preferences."""
        # Arrange
        user_id = str(sample_user_feed_day.user_id)
        mock_scalars = Mock()
        mock_scalars.all.return_value = [sample_user_feed_day]
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        # Act
        result = await user_repository.get_user_feed_days(user_id)

        # Assert
        assert len(result) == 1
        assert result[0] == sample_user_feed_day
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_feed_day_existing(
        self, user_repository, mock_db, sample_user_feed_day
    ):
        """Test updating an existing user feed day preference."""
        # Arrange
        user_id = str(sample_user_feed_day.user_id)
        feed_id = str(sample_user_feed_day.feed_id)
        new_day_id = str(uuid.uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = sample_user_feed_day
        mock_db.execute.return_value = mock_result

        # Act
        result = await user_repository.update_user_feed_day(
            user_id, feed_id, new_day_id
        )

        # Assert
        assert result == sample_user_feed_day
        assert str(result.day_id) == new_day_id
        mock_db.add.assert_called_once_with(sample_user_feed_day)

    @pytest.mark.asyncio
    async def test_update_user_feed_day_new(self, user_repository, mock_db):
        """Test creating a new user feed day preference."""
        # Arrange
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        # Act
        result = await user_repository.update_user_feed_day(user_id, feed_id, day_id)

        # Assert
        assert isinstance(result, UserFeedDay)
        assert str(result.user_id) == user_id
        assert str(result.feed_id) == feed_id
        assert str(result.day_id) == day_id
        mock_db.add.assert_called_once_with(result)

    @pytest.mark.asyncio
    async def test_ensure_user_feed_days_creates_missing_preferences(
        self, user_repository, mock_db
    ):
        """Ensure missing feed day preferences are created."""
        user_id = uuid.uuid4()
        feeds = [Mock(feed_id=uuid.uuid4()) for _ in range(3)]
        default_day = Mock(day_id=uuid.uuid4())

        mock_scalars = Mock()
        mock_scalars.all.return_value = []
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        await user_repository.ensure_user_feed_days(str(user_id), feeds, default_day)

        mock_db.execute.assert_called_once()
        assert mock_db.add.call_count == len(feeds)
        added_records = [call.args[0] for call in mock_db.add.call_args_list]
        assert all(record.user_id == user_id for record in added_records)
        assert all(record.day_id == default_day.day_id for record in added_records)
        mock_db.flush.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile_success(
        self, user_repository, mock_db, sample_user, monkeypatch
    ):
        async def fake_validate_user_exists(**kwargs):
            return sample_user

        monkeypatch.setattr(
            "app.api.repositories.user.user_repository.validate_user_exists",
            fake_validate_user_exists,
        )

        new_name = "GardenGuru"
        new_country = "FR"

        result = await user_repository.update_user_profile(
            str(sample_user.user_id), new_name, new_country
        )

        assert result is sample_user
        assert sample_user.user_first_name == new_name
        assert sample_user.user_country_code == new_country

    @pytest.mark.asyncio
    async def test_get_active_varieties_returns_sorted_list(
        self, user_repository, mock_db
    ):
        user_id = uuid.uuid4()
        varieties = [
            UserActiveVariety(user_id=user_id, variety_id=uuid.uuid4())
            for _ in range(2)
        ]

        mock_scalars = Mock()
        mock_scalars.all.return_value = varieties
        mock_result = Mock()
        mock_result.scalars.return_value = mock_scalars
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_active_varieties(str(user_id))

        assert result == varieties
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_active_variety_success(self, user_repository, mock_db):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        association = UserActiveVariety(user_id=user_id, variety_id=variety_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = association
        mock_db.execute.return_value = mock_result

        result = await user_repository.get_active_variety(user_id, variety_id)

        assert result is association
        mock_db.execute.assert_called_once()

    @pytest.mark.asyncio
    async def test_add_active_variety_flushes_and_refreshes(
        self, user_repository, mock_db
    ):
        association = UserActiveVariety(user_id=uuid.uuid4(), variety_id=uuid.uuid4())

        result = await user_repository.add_active_variety(association)

        assert result is association
        mock_db.add.assert_called_once_with(association)
        mock_db.flush.assert_called_once()
        mock_db.refresh.assert_awaited_once_with(
            association, attribute_names=["variety"]
        )

    @pytest.mark.asyncio
    async def test_delete_active_variety_success(self, user_repository, mock_db):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()
        association = UserActiveVariety(user_id=user_id, variety_id=variety_id)

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = association
        mock_db.execute.return_value = mock_result

        result = await user_repository.delete_active_variety(user_id, variety_id)

        assert result is True
        mock_db.delete.assert_awaited_once_with(association)
        mock_db.flush.assert_called()

    @pytest.mark.asyncio
    async def test_delete_active_variety_not_found(self, user_repository, mock_db):
        user_id = uuid.uuid4()
        variety_id = uuid.uuid4()

        mock_result = Mock()
        mock_result.scalar_one_or_none.return_value = None
        mock_db.execute.return_value = mock_result

        result = await user_repository.delete_active_variety(user_id, variety_id)

        assert result is False
        mock_db.delete.assert_not_called()
