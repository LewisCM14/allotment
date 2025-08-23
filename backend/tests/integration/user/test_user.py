import uuid
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest

from app.api.core.auth_utils import create_token
from app.api.core.config import settings
from app.api.middleware.exception_handler import BaseApplicationError

AUTH_PREFIX = f"{settings.API_PREFIX}/auth"
USER_PREFIX = f"{settings.API_PREFIX}/users"


class TestVerificationStatus:
    @pytest.mark.asyncio
    async def test_request_verification_email_success(self, client, mocker):
        mock_ctx = AsyncMock()
        mock_ctx.send_verification_email_service = AsyncMock()
        mocker.patch(
            "app.api.v1.user.user.UserUnitOfWork",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_ctx),
                __aexit__=AsyncMock(return_value=None),
            ),
        )
        resp = await client.post(
            f"{USER_PREFIX}/email-verifications",
            json={"user_email": "test@example.com"},
        )
        assert resp.status_code == 200
        assert "Verification email sent successfully" in resp.json()["message"]
        mock_ctx.send_verification_email_service.assert_called_once_with(
            "test@example.com"
        )

    @pytest.mark.asyncio
    async def test_check_verification_status_success(self, client, mocker):
        from app.api.schemas.user.user_schema import VerificationStatusResponse

        verification = VerificationStatusResponse(
            is_email_verified=True, user_id="verif-123"
        )
        mock_ctx = AsyncMock()
        mock_ctx.get_verification_status_service.return_value = verification
        mocker.patch(
            "app.api.v1.user.user.UserUnitOfWork",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=mock_ctx),
                __aexit__=AsyncMock(return_value=None),
            ),
        )
        resp = await client.get(
            f"{USER_PREFIX}/verification-status",
            params={"user_email": "any@example.com"},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["is_email_verified"] is True and data["user_id"] == "verif-123"


class TestPasswordReset:
    @pytest.mark.asyncio
    async def test_request_password_reset_nonexistent_user(self, client):
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets", json={"user_email": "ghost@example.com"}
        )
        assert resp.status_code == 200
        assert "If your email exists" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_unverified_user(self, client, mocker):
        class Unverified:
            user_id = "u-unver"
            user_email = "unverified@example.com"
            is_email_verified = False

        # Patch DB execute to return an object whose scalar_one_or_none returns an Unverified user
        mock_result = SimpleNamespace(scalar_one_or_none=lambda: Unverified())
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            AsyncMock(return_value=mock_result),
        )
        send_ver = mocker.patch("app.api.v1.auth.send_verification_email")
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "unverified@example.com"},
        )
        assert resp.status_code == 200
        assert "verification email has been sent" in resp.json()["message"].lower()
        send_ver.assert_called_once()

    @pytest.mark.asyncio
    async def test_request_password_reset_verified_success(self, client, mocker):
        class Verified:
            user_id = "u-ver"
            user_email = "verified@example.com"
            is_email_verified = True

        mock_result = SimpleNamespace(scalar_one_or_none=lambda: Verified())
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            AsyncMock(return_value=mock_result),
        )
        mock_uow_cls = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        ctx = AsyncMock()
        ctx.request_password_reset.return_value = {
            "status": "success",
            "message": "Password reset link sent",
        }
        mock_uow_cls.return_value.__aenter__.return_value = ctx
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )
        assert resp.status_code == 200
        assert "Password reset link sent" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_request_password_reset_general_exception(self, client, mocker):
        class Verified:
            user_id = "u-ver"
            user_email = "verified@example.com"
            is_email_verified = True

        mock_result = SimpleNamespace(scalar_one_or_none=lambda: Verified())
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            AsyncMock(return_value=mock_result),
        )
        mock_uow_cls = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        ctx = AsyncMock()
        ctx.request_password_reset.side_effect = Exception("boom")
        mock_uow_cls.return_value.__aenter__.return_value = ctx
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )
        assert resp.status_code == 500
        assert "unexpected error" in resp.json()["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_request_password_reset_base_application_error(self, client, mocker):
        class Verified:
            user_id = "u-ver"
            user_email = "verified@example.com"
            is_email_verified = True

        mock_result = SimpleNamespace(scalar_one_or_none=lambda: Verified())
        mocker.patch(
            "sqlalchemy.ext.asyncio.AsyncSession.execute",
            AsyncMock(return_value=mock_result),
        )
        mock_uow_cls = mocker.patch("app.api.v1.auth.UserUnitOfWork")
        ctx = AsyncMock()
        ctx.request_password_reset.side_effect = BaseApplicationError(
            message="A base error occurred", error_code="TEST_ERROR"
        )
        mock_uow_cls.return_value.__aenter__.return_value = ctx
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets",
            json={"user_email": "verified@example.com"},
        )
        assert resp.status_code == 400
        assert "base error" in resp.json()["detail"][0]["msg"].lower()

    @pytest.mark.asyncio
    async def test_reset_password_malformed_token(self, client):
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets/malformed-token",
            json={"new_password": "NewPassword123!"},
        )
        assert resp.status_code == 401
        assert "Internal server error" in resp.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_base_application_error(self, client, mocker):
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            ctx = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = ctx
            ctx.reset_password.side_effect = BaseApplicationError(
                message="Reset failed", status_code=400, error_code="RESET_ERROR"
            )
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{AUTH_PREFIX}/password-resets/{token}",
                json={"new_password": "NewPassword123!"},
            )
            assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_reset_password_validation_error(self, client, mocker):
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            ctx = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = ctx
            from app.api.middleware.exception_handler import BaseApplicationError

            ctx.reset_password.side_effect = BaseApplicationError(
                message="Password too weak", status_code=422, error_code="VALIDATION"
            )
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{AUTH_PREFIX}/password-resets/{token}",
                json={"new_password": "weak"},
            )
            assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_reset_password_invalid_token_error(self, client, mocker):
        from app.api.middleware.exception_handler import InvalidTokenError

        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            ctx = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = ctx
            ctx.reset_password.side_effect = InvalidTokenError("Invalid token")
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{AUTH_PREFIX}/password-resets/{token}",
                json={"new_password": "NewPassword123!"},
            )
            assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_reset_password_general_exception(self, client, mocker):
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            ctx = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = ctx
            ctx.reset_password.side_effect = Exception("Unexpected error")
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{AUTH_PREFIX}/password-resets/{token}",
                json={"new_password": "NewPassword123!"},
            )
            assert resp.status_code == 500
            assert "Internal server error" in resp.json()["detail"][0]["msg"]

    @pytest.mark.asyncio
    async def test_reset_password_success(self, client, mocker):
        with patch("app.api.v1.auth.UserUnitOfWork") as mock_uow:
            ctx = AsyncMock()
            mock_uow.return_value.__aenter__.return_value = ctx
            ctx.reset_password.return_value = None
            token = create_token(user_id=str(uuid.uuid4()), token_type="reset")
            resp = await client.post(
                f"{AUTH_PREFIX}/password-resets/{token}",
                json={"new_password": "NewPassword123!"},
            )
            assert resp.status_code == 200
            assert "Password has been reset successfully" in resp.json()["message"]

    @pytest.mark.asyncio
    async def test_reset_password_decode_exception(self, client, mocker):
        mocker.patch(
            "app.api.core.auth_utils.decode_token", side_effect=Exception("boom")
        )
        resp = await client.post(
            f"{AUTH_PREFIX}/password-resets/sometoken",
            json={"new_password": "NewPassword123!"},
        )
        assert resp.status_code == 401
        assert "Internal server error" in resp.json()["detail"][0]["msg"]


class TestUserProfile:
    @pytest.mark.asyncio
    async def test_get_user_profile_success(self, client, register_user):
        headers = await register_user("profile_get")
        resp = await client.get(f"{USER_PREFIX}/profile", headers=headers)
        assert resp.status_code == 200
        data = resp.json()
        assert {
            "user_id",
            "user_email",
            "user_first_name",
            "user_country_code",
            "is_email_verified",
        } <= data.keys()

    @pytest.mark.asyncio
    async def test_get_user_profile_unauthorized(self, client):
        resp = await client.get(f"{USER_PREFIX}/profile")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile_success(self, client, register_user, mocker):
        headers = await register_user("profile_upd")
        updated = SimpleNamespace(
            user_id=uuid.uuid4(),
            user_email="profile_upd@example.com",
            user_first_name="Updated Name",
            user_country_code="US",
            is_email_verified=True,
        )
        ctx = AsyncMock()
        ctx.update_user_profile.return_value = updated
        mocker.patch(
            "app.api.v1.user.user.UserUnitOfWork",
            return_value=AsyncMock(
                __aenter__=AsyncMock(return_value=ctx),
                __aexit__=AsyncMock(return_value=None),
            ),
        )
        resp = await client.put(
            f"{USER_PREFIX}/profile",
            json={"user_first_name": "Updated Name", "user_country_code": "US"},
            headers=headers,
        )
        assert resp.status_code == 200
        data = resp.json()
        assert (
            data["user_first_name"] == "Updated Name"
            and data["user_country_code"] == "US"
        )
        ctx.update_user_profile.assert_called_once()

    @pytest.mark.asyncio
    async def test_update_user_profile_unauthorized(self, client):
        resp = await client.put(
            f"{USER_PREFIX}/profile",
            json={"user_first_name": "Name", "user_country_code": "US"},
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_update_user_profile_validation_errors(self, client, register_user):
        headers = await register_user("profile_invalid")
        resp = await client.put(
            f"{USER_PREFIX}/profile",
            json={"user_first_name": "X", "user_country_code": "USA"},
            headers=headers,
        )
        assert resp.status_code == 422

    @pytest.mark.asyncio
    async def test_update_user_profile_missing_fields(self, client, register_user):
        headers = await register_user("profile_missing")
        resp = await client.put(
            f"{USER_PREFIX}/profile", json={"user_country_code": "US"}, headers=headers
        )
        assert resp.status_code == 422
        resp = await client.put(
            f"{USER_PREFIX}/profile", json={"user_first_name": "Valid"}, headers=headers
        )
        assert resp.status_code == 422
