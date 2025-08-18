"""Unit tests for user.py endpoints using mocked dependencies only."""

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.middleware.exception_handler import BaseApplicationError, UserNotFoundError
from app.api.schemas.user.user_schema import (
    EmailRequest,
    MessageResponse,
    UserProfileResponse,
    UserProfileUpdate,
    VerificationStatusResponse,
)
from app.api.v1 import user
from tests.test_helpers import build_user_stub, mock_user_uow


@pytest.mark.asyncio
class TestUserEndpointsUnit:
    async def test_request_verification_email_success(self, mocker):
        uow = mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"send_verification_email_service": None},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        result = await user.request_verification_email(
            EmailRequest(user_email="test@example.com"), mock_db
        )
        assert isinstance(result, MessageResponse)
        uow.send_verification_email_service.assert_called_once_with("test@example.com")

    async def test_request_verification_email_exception(self, mocker):
        def raise_exc(user_email: str):
            raise Exception("Email service error")

        mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"send_verification_email_service": raise_exc},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        with pytest.raises(Exception, match="Email service error"):
            await user.request_verification_email(
                EmailRequest(user_email="test@example.com"), mock_db
            )

    async def test_check_verification_status_success(self, mocker):
        resp_obj = VerificationStatusResponse(
            is_email_verified=True, user_id="test-user-id"
        )
        uow = mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"get_verification_status_service": resp_obj},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        result = await user.check_verification_status("test@example.com", mock_db)
        assert result == resp_obj
        uow.get_verification_status_service.assert_called_once_with("test@example.com")

    async def test_get_user_profile_success(self, mocker):
        mock_current = build_user_stub(
            mocker, user_id="test-user-id", first_name="Test", verified=True
        )
        mock_current.user_email = "test@example.com"
        mock_current.user_country_code = "GB"
        result = await user.get_user_profile(mock_current)
        assert isinstance(result, UserProfileResponse)
        assert result.user_first_name == "Test"
        assert result.is_email_verified is True

    async def test_update_user_profile_success(self, mocker):
        mock_current = build_user_stub(mocker, user_id="test-user-id")

        class UpdatedUser:
            pass

        updated = UpdatedUser()
        updated.user_id = "test-user-id"
        updated.user_email = "test@example.com"
        updated.user_first_name = "Updated Name"
        updated.user_country_code = "US"
        updated.is_email_verified = False
        uow = mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"update_user_profile": updated},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        result = await user.update_user_profile(
            UserProfileUpdate(user_first_name="Updated Name", user_country_code="US"),
            mock_current,
            mock_db,
        )
        assert result.user_first_name == "Updated Name"
        assert result.user_country_code == "US"
        assert result.is_email_verified is False
        uow.update_user_profile.assert_awaited_once_with(
            user_id="test-user-id", first_name="Updated Name", country_code="US"
        )

    async def test_request_verification_email_user_not_found(self, mocker):
        def raise_nf(user_email: str):
            raise UserNotFoundError("User not found")

        mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"send_verification_email_service": raise_nf},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        with pytest.raises(UserNotFoundError):
            await user.request_verification_email(
                EmailRequest(user_email="missing@example.com"), mock_db
            )

    async def test_check_verification_status_user_not_found(self, mocker):
        def raise_nf(user_email: str):
            raise UserNotFoundError("User not found")

        mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"get_verification_status_service": raise_nf},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        with pytest.raises(UserNotFoundError):
            await user.check_verification_status("missing@example.com", mock_db)

    async def test_update_user_profile_uow_error(self, mocker):
        def raise_update(
            *, user_id: str, first_name: str | None, country_code: str | None
        ):
            raise BaseApplicationError(
                "Update failed", status_code=400, error_code="UPDATE_ERROR"
            )

        mock_current = build_user_stub(mocker, user_id="test-user-id")
        mock_user_uow(
            mocker,
            path="app.api.v1.user.UserUnitOfWork",
            methods={"update_user_profile": raise_update},
        )
        mock_db = mocker.MagicMock(spec=AsyncSession)
        with pytest.raises(BaseApplicationError):
            await user.update_user_profile(
                UserProfileUpdate(
                    user_first_name="Updated Name", user_country_code="US"
                ),
                mock_current,
                mock_db,
            )
