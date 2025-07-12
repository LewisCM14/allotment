"""
Unit tests for user_auth.py endpoints (login, refresh_token).
All dependencies are mocked. These tests cover logic, not integration.
"""

from unittest.mock import MagicMock

import pytest
from fastapi import Request
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
    InvalidTokenError,
)
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import RefreshRequest, UserLogin
from app.api.v1 import user_auth


@pytest.mark.asyncio
class TestLoginEndpointUnit:
    async def test_login_success(self, mocker):
        mock_user = MagicMock()
        mock_user.user_id = "user-id"
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = True
        mocker.patch("app.api.v1.user_auth.authenticate_user", return_value=mock_user)
        mocker.patch(
            "app.api.v1.user_auth.create_token", side_effect=["access", "refresh"]
        )
        mocker.patch("app.api.v1.user_auth.log_timing")
        mocker.patch("app.api.v1.user_auth.logger")
        # Mock the safe_operation import and context manager
        mock_safe_operation = mocker.patch(
            "app.api.middleware.error_handler.safe_operation"
        )
        mock_safe_operation.return_value.__aenter__.return_value = None
        mock_safe_operation.return_value.__aexit__.return_value = False
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        user = UserLogin(user_email="a@b.com", user_password="SecurePass123!")
        db = MagicMock(spec=AsyncSession)
        result = await user_auth.login(request, user, db)
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access"
        assert result.refresh_token == "refresh"
        assert result.user_first_name == "Test"
        assert result.is_email_verified is True
        assert result.user_id == "user-id"

    async def test_login_invalid_credentials(self, mocker):
        mocker.patch("app.api.v1.user_auth.authenticate_user", return_value=None)
        # Mock the safe_operation import and context manager
        mock_safe_operation = mocker.patch(
            "app.api.middleware.error_handler.safe_operation"
        )
        mock_safe_operation.return_value.__aenter__.return_value = None
        mock_safe_operation.return_value.__aexit__.return_value = False
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        user = UserLogin(user_email="a@b.com", user_password="SecurePass123!")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(AuthenticationError):
            await user_auth.login(request, user, db)

    async def test_login_authenticate_user_raises_base_error(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.authenticate_user",
            side_effect=BaseApplicationError("fail", "fail_code"),
        )
        # Mock the safe_operation import and context manager
        mock_safe_operation = mocker.patch(
            "app.api.middleware.error_handler.safe_operation"
        )
        mock_safe_operation.return_value.__aenter__.return_value = None
        mock_safe_operation.return_value.__aexit__.return_value = False
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        user = UserLogin(user_email="a@b.com", user_password="SecurePass123!")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(BaseApplicationError):
            await user_auth.login(request, user, db)

    async def test_login_authenticate_user_raises_general_exception(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.authenticate_user", side_effect=Exception("fail")
        )
        # Mock the safe_operation import and context manager
        mock_safe_operation = mocker.patch(
            "app.api.middleware.error_handler.safe_operation"
        )
        mock_safe_operation.return_value.__aenter__.return_value = None
        mock_safe_operation.return_value.__aexit__.return_value = False
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        user = UserLogin(user_email="a@b.com", user_password="SecurePass123!")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(Exception):
            await user_auth.login(request, user, db)

    async def test_login_token_generation_exception(self, mocker):
        mock_user = MagicMock()
        mock_user.user_id = "user-id"
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = True
        mocker.patch("app.api.v1.user_auth.authenticate_user", return_value=mock_user)
        mocker.patch(
            "app.api.v1.user_auth.create_token",
            side_effect=Exception("Token generation failed"),
        )
        mocker.patch("app.api.v1.user_auth.log_timing")
        mocker.patch("app.api.v1.user_auth.logger")
        # Mock the safe_operation import and context manager
        mock_safe_operation = mocker.patch(
            "app.api.middleware.error_handler.safe_operation"
        )
        mock_safe_operation.return_value.__aenter__.return_value = None
        mock_safe_operation.return_value.__aexit__.return_value = False
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        user = UserLogin(user_email="a@b.com", user_password="SecurePass123!")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(Exception):
            await user_auth.login(request, user, db)


@pytest.mark.asyncio
class TestRefreshTokenEndpointUnit:
    async def test_refresh_token_success(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.decode_token",
            return_value={"type": "refresh", "sub": "user-id"},
        )
        mock_user = MagicMock()
        mock_user.user_id = "user-id"
        mock_user.user_first_name = "Test"
        mock_user.is_email_verified = True
        mocker.patch(
            "app.api.v1.user_auth.validate_user_exists", return_value=mock_user
        )
        mocker.patch(
            "app.api.v1.user_auth.create_token", side_effect=["access", "refresh"]
        )
        mocker.patch("app.api.v1.user_auth.logger")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        refresh_data = RefreshRequest(refresh_token="token")
        db = MagicMock(spec=AsyncSession)
        result = await user_auth.refresh_token(request, refresh_data, db)
        assert isinstance(result, TokenResponse)
        assert result.access_token == "access"
        assert result.refresh_token == "refresh"
        assert result.user_first_name == "Test"
        assert result.is_email_verified is True
        assert result.user_id == "user-id"

    async def test_refresh_token_invalid_type(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.decode_token",
            return_value={"type": "access", "sub": "user-id"},
        )
        mocker.patch("app.api.v1.user_auth.logger")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        refresh_data = RefreshRequest(refresh_token="token")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(InvalidTokenError):
            await user_auth.refresh_token(request, refresh_data, db)

    async def test_refresh_token_missing_sub(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.decode_token", return_value={"type": "refresh"}
        )
        mocker.patch("app.api.v1.user_auth.logger")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        refresh_data = RefreshRequest(refresh_token="token")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(InvalidTokenError):
            await user_auth.refresh_token(request, refresh_data, db)

    async def test_refresh_token_validate_user_exists_raises(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.decode_token",
            return_value={"type": "refresh", "sub": "user-id"},
        )
        mocker.patch(
            "app.api.v1.user_auth.validate_user_exists",
            side_effect=BaseApplicationError("fail", "fail_code"),
        )
        mocker.patch("app.api.v1.user_auth.logger")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        refresh_data = RefreshRequest(refresh_token="token")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(BaseApplicationError):
            await user_auth.refresh_token(request, refresh_data, db)

    async def test_refresh_token_decode_token_raises(self, mocker):
        mocker.patch(
            "app.api.v1.user_auth.decode_token",
            side_effect=InvalidTokenError("Token decode error"),
        )
        mocker.patch("app.api.v1.user_auth.logger")
        mock_ctx = MagicMock()
        mock_ctx.get.return_value = "reqid"
        mocker.patch("app.api.v1.user_auth.request_id_ctx_var", mock_ctx)
        request = MagicMock(spec=Request)
        refresh_data = RefreshRequest(refresh_token="token")
        db = MagicMock(spec=AsyncSession)
        with pytest.raises(InvalidTokenError):
            await user_auth.refresh_token(request, refresh_data, db)
