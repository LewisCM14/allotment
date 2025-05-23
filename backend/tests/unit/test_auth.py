"""
Auth module unit tests.
"""

import uuid
from datetime import UTC, datetime, timedelta
from unittest.mock import MagicMock, patch

import bcrypt
import pytest
from authlib.jose import JoseError, jwt
from fastapi import HTTPException

from app.api.core.auth import (
    authenticate_user,
    create_token,
    get_current_user,
    verify_password,
)
from app.api.core.config import settings
from app.api.models import User


class TestPasswordVerification:
    """Tests for password verification functionality."""

    @pytest.mark.asyncio
    async def test_password_hashing(self):
        """Test that passwords are properly hashed and verified."""
        plain_password = "SecurePass123!"
        hashed_password = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        assert isinstance(hashed_password, str)
        assert verify_password(plain_password, hashed_password) is True
        assert verify_password("WrongPassword", hashed_password) is False

    @pytest.mark.asyncio
    async def test_verify_password_edge_cases(self):
        """Test verify_password with edge cases."""
        plain_password = "SecurePass123!"
        hashed_password = bcrypt.hashpw(
            plain_password.encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")

        assert verify_password("", hashed_password) is False

        long_password = "x" * 1000
        assert verify_password(long_password, hashed_password) is False

    @pytest.mark.asyncio
    async def test_verify_password_error_handling(self):
        """Test error handling in verify_password."""
        assert verify_password("password", "invalid-hash-format") is False


class TestTokenCreation:
    """Tests for JWT token creation functionality."""

    @pytest.mark.asyncio
    async def test_create_token_access(self):
        """Test creating an access token."""
        user_id = str(uuid.uuid4())
        token = create_token(user_id=user_id, token_type="access")

        payload = jwt.decode(token, settings.PUBLIC_KEY)

        assert payload["sub"] == user_id
        assert payload["type"] == "access"
        assert "exp" in payload
        assert "iat" in payload
        assert "jti" in payload

    @pytest.mark.asyncio
    async def test_create_token_refresh(self):
        """Test creating a refresh token."""
        user_id = str(uuid.uuid4())
        token = create_token(user_id=user_id, token_type="refresh")

        payload = jwt.decode(token, settings.PUBLIC_KEY)

        assert payload["sub"] == user_id
        assert payload["type"] == "refresh"
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_create_token_reset(self):
        """Test creating a password reset token."""
        user_id = str(uuid.uuid4())
        token = create_token(user_id=user_id, token_type="reset")

        payload = jwt.decode(token, settings.PUBLIC_KEY)

        assert payload["sub"] == user_id
        assert payload["type"] == "reset"
        assert "exp" in payload

    @pytest.mark.asyncio
    async def test_create_token_custom_expiry(self):
        """Test creating a token with custom expiry time."""
        user_id = str(uuid.uuid4())
        expiry_seconds = 300
        token = create_token(user_id=user_id, expiry_seconds=expiry_seconds)

        payload = jwt.decode(token, settings.PUBLIC_KEY)

        expected_exp = datetime.now(UTC) + timedelta(seconds=expiry_seconds)
        assert abs(payload["exp"] - expected_exp.timestamp()) < 2

    @pytest.mark.asyncio
    async def test_create_token_expires_delta(self):
        """Test creating a token with expires_delta."""
        user_id = str(uuid.uuid4())
        expires_delta = timedelta(minutes=30)
        token = create_token(user_id=user_id, expires_delta=expires_delta)

        payload = jwt.decode(token, settings.PUBLIC_KEY)

        expected_exp = datetime.now(UTC) + expires_delta
        assert abs(payload["exp"] - expected_exp.timestamp()) < 2

    @pytest.mark.asyncio
    @patch("app.api.core.auth.jwt.encode")
    async def test_create_token_exception(self, mock_encode):
        """Test error handling in create_token."""
        mock_encode.side_effect = JoseError("JWT encoding error")

        user_id = str(uuid.uuid4())

        with pytest.raises(JoseError):
            create_token(user_id=user_id)


class TestUserAuthentication:
    """Tests for user authentication functionality."""

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self):
        """Test successful authentication."""
        mock_user = MagicMock(spec=User)
        mock_user.user_password_hash = bcrypt.hashpw(
            "correct_password".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        mock_user.user_id = uuid.uuid4()

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        result = authenticate_user(mock_db, "user@example.com", "correct_password")

        assert result is mock_user
        mock_db.query.assert_called_once_with(User)
        mock_query.filter.assert_called_once()

    @pytest.mark.asyncio
    async def test_authenticate_user_wrong_password(self):
        """Test authentication with wrong password."""
        mock_user = MagicMock(spec=User)
        mock_user.user_password_hash = bcrypt.hashpw(
            "correct_password".encode("utf-8"), bcrypt.gensalt()
        ).decode("utf-8")
        mock_user.user_id = uuid.uuid4()

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        result = authenticate_user(mock_db, "user@example.com", "wrong_password")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_nonexistent(self):
        """Test authentication with non-existent user."""
        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        result = authenticate_user(mock_db, "nonexistent@example.com", "any_password")

        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_exception(self):
        """Test error handling in authenticate_user."""
        mock_db = MagicMock()
        mock_db.query.side_effect = Exception("Database error")

        result = authenticate_user(mock_db, "user@example.com", "password")

        assert result is None


class TestCurrentUserValidation:
    """Tests for current user validation functionality."""

    @pytest.mark.asyncio
    @patch("app.api.core.auth.jwt.decode")
    async def test_get_current_user_success(self, mock_decode):
        """Test get_current_user with valid token."""
        user_id = str(uuid.uuid4())
        mock_decode.return_value = {"sub": user_id}

        mock_user = MagicMock(spec=User)
        mock_user.user_id = user_id

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = mock_user

        result = get_current_user("valid_token", mock_db)

        assert result is mock_user
        mock_decode.assert_called_once_with("valid_token", settings.PUBLIC_KEY)

    @pytest.mark.asyncio
    @patch("app.api.core.auth.jwt.decode")
    async def test_get_current_user_invalid_token(self, mock_decode):
        """Test get_current_user with invalid token."""
        mock_decode.side_effect = JoseError("Invalid token")

        with pytest.raises(HTTPException) as exc_info:
            get_current_user("invalid_token", MagicMock())

        assert exc_info.value.status_code == 401
        assert "Invalid token" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.core.auth.jwt.decode")
    async def test_get_current_user_missing_sub(self, mock_decode):
        """Test get_current_user with token missing sub claim."""
        mock_decode.return_value = {}

        with pytest.raises(HTTPException) as exc_info:
            get_current_user("token_without_sub", MagicMock())

        assert exc_info.value.status_code == 401
        assert "Invalid token payload" in exc_info.value.detail

    @pytest.mark.asyncio
    @patch("app.api.core.auth.jwt.decode")
    async def test_get_current_user_user_not_found(self, mock_decode):
        """Test get_current_user with token for non-existent user."""
        user_id = str(uuid.uuid4())
        mock_decode.return_value = {"sub": user_id}

        mock_db = MagicMock()
        mock_query = mock_db.query.return_value
        mock_filter = mock_query.filter.return_value
        mock_filter.first.return_value = None

        with pytest.raises(HTTPException) as exc_info:
            get_current_user("valid_token", mock_db)

        assert exc_info.value.status_code == 404
        assert "User not found" in exc_info.value.detail
