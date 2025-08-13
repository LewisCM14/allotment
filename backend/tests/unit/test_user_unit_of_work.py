import uuid
from unittest.mock import AsyncMock, patch

import pytest
from authlib.jose.errors import JoseError
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import InvalidTokenError
from app.api.models.user.user_model import User, UserAllotment
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_allotment_schema import (
    UserAllotmentCreate,
    UserAllotmentUpdate,
)
from app.api.schemas.user.user_schema import UserCreate
from app.api.services.user.user_unit_of_work import UserUnitOfWork


class TestUserUnitOfWork:
    """Test suite for UserUnitOfWork."""

    @pytest.fixture
    def mock_db(self):
        """Create a mock database session."""
        return AsyncMock(spec=AsyncSession)

    @pytest.fixture
    def user_unit_of_work(self, mock_db):
        """Create a UserUnitOfWork instance with mock database."""
        return UserUnitOfWork(db=mock_db)

    @pytest.fixture
    def sample_user(self):
        """Create a sample user."""
        user = User()
        user.user_id = uuid.uuid4()
        user.user_email = "test@example.com"
        user.user_password_hash = "hashed_password"
        user.user_first_name = "Test"
        user.user_country_code = "US"
        user.is_email_verified = True
        return user

    @pytest.fixture
    def sample_user_create(self):
        """Create a sample user create schema."""
        return UserCreate(
            user_email="test@example.com",
            user_password="test_password",
            user_first_name="Test",
            user_country_code="US",
        )

    @pytest.fixture
    def sample_allotment(self):
        """Create a sample user allotment."""
        allotment = UserAllotment(
            user_allotment_id=uuid.uuid4(),
            user_id=uuid.uuid4(),
            allotment_postal_zip_code="12345",
            allotment_width_meters=10.0,
            allotment_length_meters=10.0,
        )
        return allotment

    def test_init(self, mock_db):
        """Test unit of work initialization."""
        uow = UserUnitOfWork(db=mock_db)
        assert uow.db == mock_db
        assert isinstance(uow.user_repo, UserRepository)

    @pytest.mark.asyncio
    async def test_context_manager_success(self, mock_db):
        """Test context manager successful transaction."""
        uow = UserUnitOfWork(db=mock_db)

        async with uow:
            # Mock some operation
            pass

        mock_db.commit.assert_called_once()
        mock_db.rollback.assert_not_called()

    @pytest.mark.asyncio
    async def test_context_manager_exception(self, mock_db):
        """Test context manager with exception triggers rollback."""
        uow = UserUnitOfWork(db=mock_db)

        with pytest.raises(ValueError):
            async with uow:
                raise ValueError("Test exception")

        mock_db.rollback.assert_called_once()
        mock_db.commit.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.UserFactory.create_user")
    @patch("app.api.services.user.user_unit_of_work.send_verification_email")
    async def test_register_user_success(
        self,
        mock_send_email,
        mock_create_user,
        user_unit_of_work,
        sample_user_create,
        sample_user,
    ):
        """Test successful user registration."""
        mock_create_user.return_value = sample_user
        mock_send_email.return_value = None

        with patch.object(
            user_unit_of_work.user_repo, "create_user", return_value=sample_user
        ) as mock_repo_create:
            result = await user_unit_of_work.register_user(sample_user_create)

        assert result == sample_user
        mock_create_user.assert_called_once_with(sample_user_create)
        mock_repo_create.assert_called_once_with(sample_user)
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.UserFactory.create_user")
    async def test_register_user_creation_error(
        self, mock_create_user, user_unit_of_work, sample_user_create
    ):
        """Test user registration with creation error."""
        mock_create_user.side_effect = ValueError("User creation failed")

        with pytest.raises(ValueError, match="User creation failed"):
            await user_unit_of_work.register_user(sample_user_create)

    @pytest.mark.asyncio
    async def test_verify_user_email_success(self, user_unit_of_work, sample_user):
        """Test successful email verification."""
        user_id = str(sample_user.user_id)

        with patch.object(
            user_unit_of_work.user_repo, "verify_email", return_value=sample_user
        ) as mock_verify:
            result = await user_unit_of_work.verify_user_email(user_id)

        assert result == sample_user
        mock_verify.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_verify_user_email_invalid_token(self, user_unit_of_work):
        """Test email verification with invalid token."""
        user_id = "invalid-user-id"

        with patch.object(
            user_unit_of_work.user_repo,
            "verify_email",
            side_effect=InvalidTokenError("Invalid token"),
        ):
            with pytest.raises(InvalidTokenError, match="Invalid token"):
                await user_unit_of_work.verify_user_email(user_id)

    @pytest.mark.asyncio
    async def test_get_user_by_email(self, user_unit_of_work, sample_user):
        """Test getting user by email."""
        email = sample_user.user_email

        with patch.object(
            user_unit_of_work.user_repo, "get_user_by_email", return_value=sample_user
        ) as mock_get:
            result = await user_unit_of_work.get_user_by_email(email)

            assert result == sample_user
            mock_get.assert_called_once_with(email)

    @pytest.mark.asyncio
    async def test_get_user_by_email_not_found(self, user_unit_of_work):
        """Test getting user by email when not found."""
        email = "nonexistent@example.com"

        with patch.object(
            user_unit_of_work.user_repo, "get_user_by_email", return_value=None
        ) as mock_get:
            result = await user_unit_of_work.get_user_by_email(email)

            assert result is None
            mock_get.assert_called_once_with(email)

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.send_password_reset_email")
    async def test_request_password_reset_success(
        self, mock_send_email, user_unit_of_work, sample_user
    ):
        """Test successful password reset request."""
        email = sample_user.user_email
        mock_send_email.return_value = None

        with patch.object(
            user_unit_of_work.user_repo, "get_user_by_email", return_value=sample_user
        ) as mock_get:
            await user_unit_of_work.request_password_reset(email)

        mock_get.assert_called_once_with(email)
        mock_send_email.assert_called_once()

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.send_password_reset_email")
    async def test_request_password_reset_user_not_found(
        self, mock_send_email, user_unit_of_work
    ):
        """Test password reset request for non-existent user."""
        email = "nonexistent@example.com"

        with patch.object(
            user_unit_of_work.user_repo, "get_user_by_email", return_value=None
        ) as mock_get:
            await user_unit_of_work.request_password_reset(email)

        mock_get.assert_called_once_with(email)
        # Should still not raise error for security reasons
        mock_send_email.assert_not_called()

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.jwt")
    async def test_reset_password_success(
        self, mock_jwt, user_unit_of_work, sample_user
    ):
        """Test successful password reset."""
        token = "valid_token"
        new_password = "NewPassword123!"
        user_id = str(sample_user.user_id)

        # Mock JWT decode
        mock_jwt.decode.return_value = {
            "user_id": user_id,
            "type": "reset",
            "sub": user_id,
        }

        with patch.object(
            user_unit_of_work.user_repo,
            "update_user_password",
            return_value=sample_user,
        ) as mock_update:
            result = await user_unit_of_work.reset_password(token, new_password)

        assert result == sample_user
        mock_jwt.decode.assert_called_once()
        mock_update.assert_called_once_with(user_id, new_password)

    @pytest.mark.asyncio
    @patch("app.api.services.user.user_unit_of_work.jwt")
    async def test_reset_password_invalid_token(self, mock_jwt, user_unit_of_work):
        """Test password reset with invalid token."""
        token = "invalid_token"
        new_password = "NewPassword123!"

        mock_jwt.decode.side_effect = JoseError("Invalid token")

        with pytest.raises(InvalidTokenError, match="Invalid token:"):
            await user_unit_of_work.reset_password(token, new_password)

    @pytest.mark.asyncio
    async def test_create_user_allotment(self, user_unit_of_work, sample_allotment):
        """Test creating a user allotment."""
        user_id = str(sample_allotment.user_id)
        allotment_data = UserAllotmentCreate(
            allotment_postal_zip_code="12345",
            allotment_width_meters=10.0,
            allotment_length_meters=10.0,
        )

        with patch.object(
            user_unit_of_work.user_repo,
            "create_user_allotment",
            return_value=sample_allotment,
        ) as mock_create:
            result = await user_unit_of_work.create_user_allotment(
                user_id, allotment_data
            )

        assert result == sample_allotment
        mock_create.assert_called_once_with(user_id, allotment_data)

    @pytest.mark.asyncio
    async def test_get_user_allotment(self, user_unit_of_work, sample_allotment):
        """Test getting a user allotment."""
        user_id = str(sample_allotment.user_id)

        with patch.object(
            user_unit_of_work.user_repo,
            "get_user_allotment",
            return_value=sample_allotment,
        ) as mock_get:
            result = await user_unit_of_work.get_user_allotment(user_id)

        assert result == sample_allotment
        mock_get.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_user_allotment(self, user_unit_of_work, sample_allotment):
        """Test updating a user allotment."""
        user_id = str(sample_allotment.user_id)
        allotment_data = UserAllotmentUpdate(
            allotment_postal_zip_code="54321",
            allotment_width_meters=15.0,
            allotment_length_meters=15.0,
        )

        # Create an updated allotment mock
        updated_allotment = UserAllotment()
        updated_allotment.user_allotment_id = sample_allotment.user_allotment_id
        updated_allotment.user_id = sample_allotment.user_id
        updated_allotment.allotment_postal_zip_code = (
            allotment_data.allotment_postal_zip_code
        )
        updated_allotment.allotment_width_meters = allotment_data.allotment_width_meters
        updated_allotment.allotment_length_meters = (
            allotment_data.allotment_length_meters
        )

        with patch.object(
            user_unit_of_work.user_repo,
            "update_user_allotment",
            return_value=updated_allotment,
        ) as mock_update:
            result = await user_unit_of_work.update_user_allotment(
                user_id, allotment_data
            )

        assert result == updated_allotment
        mock_update.assert_called_once_with(user_id, allotment_data)

    @pytest.mark.asyncio
    async def test_update_user_allotment_not_found(self, user_unit_of_work):
        """Test updating a user allotment that doesn't exist."""
        user_id = str(uuid.uuid4())
        allotment_data = UserAllotmentUpdate(allotment_postal_zip_code="54321")

        with patch.object(
            user_unit_of_work.user_repo,
            "update_user_allotment",
            side_effect=HTTPException(status_code=404, detail="Not found"),
        ):
            with pytest.raises(HTTPException):
                await user_unit_of_work.update_user_allotment(user_id, allotment_data)

    @pytest.mark.asyncio
    async def test_get_user_feed_days(self, user_unit_of_work):
        """Test getting user feed days."""
        user_id = str(uuid.uuid4())
        mock_user_feed_days = []

        with patch.object(
            user_unit_of_work.user_repo,
            "get_user_feed_days",
            return_value=mock_user_feed_days,
        ) as mock_get_feed_days:
            result = await user_unit_of_work.get_user_feed_days(user_id)

        assert result == mock_user_feed_days
        mock_get_feed_days.assert_called_once_with(user_id)

    @pytest.mark.asyncio
    async def test_update_user_feed_day(self, user_unit_of_work):
        """Test updating a single user feed day preference."""
        user_id = str(uuid.uuid4())
        feed_id = str(uuid.uuid4())
        day_id = str(uuid.uuid4())
        mock_result = {"updated": True}

        with patch.object(
            user_unit_of_work.user_repo,
            "update_user_feed_day",
            return_value=mock_result,
        ) as mock_update:
            result = await user_unit_of_work.update_user_feed_day(
                user_id, feed_id, day_id
            )

        assert result == mock_result
        mock_update.assert_called_once_with(user_id, feed_id, day_id)
