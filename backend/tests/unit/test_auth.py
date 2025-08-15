"""
Unit tests for auth.py endpoints (login, refresh_token).
All dependencies are mocked. These tests cover logic, not integration.

REFACTORED to use improved conftest.py fixtures and test helpers.
"""

import pytest

from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
    InvalidTokenError,
)
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import RefreshRequest, UserLogin
from app.api.v1 import auth
from tests.test_helpers import validate_token_response_schema


@pytest.mark.asyncio
class TestLoginEndpointUnit:
    async def test_login_success(
        self,
        mock_user,
        sample_user_login_data,
        mock_request_and_db,
        standard_unit_mocks,
        mock_token_creation,
        mocker,
    ):
        """Test successful login using standardized fixtures."""
        # Set up authentication mock
        mocker.patch("app.api.v1.auth.authenticate_user", return_value=mock_user)

        # Create user login object
        user = UserLogin(**sample_user_login_data)

        # Call the endpoint
        result = await auth.login(
            mock_request_and_db["request"], user, mock_request_and_db["db"]
        )

        # Validate using helper function
        assert isinstance(result, TokenResponse)
        validate_token_response_schema(result.model_dump())
        assert result.user_first_name == mock_user.user_first_name
        assert result.is_email_verified == mock_user.is_email_verified
        assert result.user_id == str(mock_user.user_id)

    async def test_login_invalid_credentials(
        self, sample_user_login_data, mock_request_and_db, standard_unit_mocks, mocker
    ):
        """Test login with invalid credentials."""
        # Mock authentication to return None (invalid credentials)
        mocker.patch("app.api.v1.auth.authenticate_user", return_value=None)

        user = UserLogin(**sample_user_login_data)

        with pytest.raises(AuthenticationError):
            await auth.login(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

    async def test_login_authenticate_user_raises_base_error(
        self, sample_user_login_data, mock_request_and_db, standard_unit_mocks, mocker
    ):
        """Test login when authenticate_user raises BaseApplicationError."""
        # Mock authentication to raise BaseApplicationError
        error = BaseApplicationError("Authentication failed", "AUTH_FAIL")
        mocker.patch("app.api.v1.auth.authenticate_user", side_effect=error)

        user = UserLogin(**sample_user_login_data)

        with pytest.raises(BaseApplicationError):
            await auth.login(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

    async def test_login_authenticate_user_raises_general_exception(
        self, sample_user_login_data, mock_request_and_db, standard_unit_mocks, mocker
    ):
        """Test login when authenticate_user raises unexpected exception."""
        mocker.patch(
            "app.api.v1.auth.authenticate_user", side_effect=Exception("Database error")
        )

        user = UserLogin(**sample_user_login_data)

        with pytest.raises(Exception):
            await auth.login(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )

    async def test_login_token_generation_exception(
        self,
        mock_user,
        sample_user_login_data,
        mock_request_and_db,
        standard_unit_mocks,
        mocker,
    ):
        """Test login when token generation fails."""
        # Mock successful authentication
        mocker.patch("app.api.v1.auth.authenticate_user", return_value=mock_user)

        # Mock token creation to fail
        mocker.patch(
            "app.api.v1.auth.create_token",
            side_effect=Exception("Token generation failed"),
        )

        user = UserLogin(**sample_user_login_data)

        with pytest.raises(Exception):
            await auth.login(
                mock_request_and_db["request"], user, mock_request_and_db["db"]
            )


@pytest.mark.asyncio
class TestRefreshTokenEndpointUnit:
    async def test_refresh_token_success(
        self, mock_user, mock_request_and_db, standard_unit_mocks, token_factory, mocker
    ):
        """Test successful token refresh."""
        # Create a valid refresh token
        refresh_token = token_factory(
            token_type="refresh", user_id=str(mock_user.user_id)
        )

        # Mock token decoding
        mocker.patch(
            "app.api.v1.auth.decode_token",
            return_value={"type": "refresh", "sub": str(mock_user.user_id)},
        )

        # Mock user validation
        mocker.patch("app.api.v1.auth.validate_user_exists", return_value=mock_user)

        # Mock new token creation
        mocker.patch(
            "app.api.v1.auth.create_token", side_effect=["new_access", "new_refresh"]
        )

        request_data = RefreshRequest(refresh_token=refresh_token)

        result = await auth.refresh_token(
            mock_request_and_db["request"], request_data, mock_request_and_db["db"]
        )

        assert isinstance(result, TokenResponse)
        validate_token_response_schema(result.model_dump())
        assert result.access_token == "new_access"
        assert result.refresh_token == "new_refresh"

    async def test_refresh_token_invalid_type(
        self, mock_request_and_db, standard_unit_mocks, token_factory, mocker
    ):
        """Test refresh token with wrong token type."""
        # Create access token instead of refresh token
        access_token = token_factory(token_type="access")

        # Mock token decoding to return access type
        mocker.patch(
            "app.api.v1.auth.decode_token",
            return_value={"type": "access", "sub": "user-id"},
        )

        request_data = RefreshRequest(refresh_token=access_token)

        with pytest.raises(InvalidTokenError):
            await auth.refresh_token(
                mock_request_and_db["request"], request_data, mock_request_and_db["db"]
            )

    async def test_refresh_token_missing_sub(
        self, mock_request_and_db, standard_unit_mocks, token_factory, mocker
    ):
        """Test refresh token with missing user ID."""
        refresh_token = token_factory(token_type="refresh")

        # Mock token decoding to return payload without 'sub'
        mocker.patch("app.api.v1.auth.decode_token", return_value={"type": "refresh"})

        request_data = RefreshRequest(refresh_token=refresh_token)

        with pytest.raises(InvalidTokenError):
            await auth.refresh_token(
                mock_request_and_db["request"], request_data, mock_request_and_db["db"]
            )

    async def test_refresh_token_validate_user_exists_raises(
        self, mock_request_and_db, standard_unit_mocks, token_factory, mocker
    ):
        """Test refresh token when user validation fails."""
        refresh_token = token_factory(token_type="refresh")

        # Mock token decoding
        mocker.patch(
            "app.api.v1.auth.decode_token",
            return_value={"type": "refresh", "sub": "nonexistent-user"},
        )

        # Mock user validation to fail
        error = BaseApplicationError("User not found", "USER_NOT_FOUND")
        mocker.patch("app.api.v1.auth.validate_user_exists", side_effect=error)

        request_data = RefreshRequest(refresh_token=refresh_token)

        with pytest.raises(BaseApplicationError):
            await auth.refresh_token(
                mock_request_and_db["request"], request_data, mock_request_and_db["db"]
            )

    async def test_refresh_token_decode_token_raises(
        self, mock_request_and_db, standard_unit_mocks, token_factory, mocker
    ):
        """Test refresh token when token decoding fails."""
        invalid_token = "invalid.token.here"

        # Mock token decoding to fail
        mocker.patch(
            "app.api.v1.auth.decode_token",
            side_effect=InvalidTokenError("Invalid token format"),
        )

        request_data = RefreshRequest(refresh_token=invalid_token)

        with pytest.raises(InvalidTokenError):
            await auth.refresh_token(
                mock_request_and_db["request"], request_data, mock_request_and_db["db"]
            )
