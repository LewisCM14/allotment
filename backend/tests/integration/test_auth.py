from unittest.mock import patch

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
)

PREFIX = settings.API_PREFIX


class TestUserLogin:
    @pytest.mark.asyncio
    async def test_login_success(self, user_factory, login_helper):
        payload = {
            "user_email": "login-success@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "Test",
            "user_country_code": "GB",
        }
        reg = await user_factory(payload)
        assert reg.status_code == 201
        login = await login_helper(payload["user_email"], payload["user_password"])
        assert login.status_code == 200
        data = login.json()
        assert {
            "access_token",
            "refresh_token",
            "token_type",
            "user_first_name",
        } <= data.keys()
        assert data["user_first_name"] == payload["user_first_name"]

    @pytest.mark.asyncio
    async def test_login_updates_last_active_date(self, user_factory, login_helper):
        payload = {
            "user_email": "datetest@example.com",
            "user_password": "SecurePass123!",
            "user_first_name": "DateTest",
            "user_country_code": "GB",
        }
        await user_factory(payload)
        first = await login_helper(payload["user_email"], payload["user_password"])
        assert first.status_code == 200
        import asyncio

        await asyncio.sleep(0.05)
        second = await login_helper(payload["user_email"], payload["user_password"])
        assert second.status_code == 200
        assert first.json()["access_token"] != second.json()["access_token"]

    @pytest.mark.asyncio
    async def test_login_invalid_credentials(self, login_helper):
        resp = await login_helper("nouser@example.com", "WrongPassword!")
        assert resp.status_code == 401
        assert resp.json()["detail"][0]["msg"] == "Invalid email or password"

    @pytest.mark.asyncio
    async def test_business_logic_error(self, login_helper, mocker):
        mock_auth = mocker.patch("app.api.v1.auth.authenticate_user")
        mock_auth.side_effect = BusinessLogicError(
            message="Account locked",
            error_code="ACCOUNT_LOCKED",
            status_code=status.HTTP_403_FORBIDDEN,
        )
        resp = await login_helper("locked@example.com", "ValidPass123!")
        assert resp.status_code == status.HTTP_403_FORBIDDEN
        assert "account locked" in str(resp.json()).lower()

    @pytest.mark.asyncio
    async def test_base_application_error(self, login_helper, mocker):
        mock_auth = mocker.patch("app.api.v1.auth.authenticate_user")
        mock_auth.side_effect = BaseApplicationError("fail", "FAIL_CODE")
        resp = await login_helper("fail@example.com", "ValidPass123!")
        assert resp.status_code == 400
        assert "FAIL_CODE" in str(resp.json())

    @pytest.mark.asyncio
    async def test_general_exception(self, login_helper, mocker):
        mock_auth = mocker.patch("app.api.v1.auth.authenticate_user")
        mock_auth.side_effect = Exception("boom")
        resp = await login_helper("err@example.com", "ValidPass123!")
        assert resp.status_code == 500

    @pytest.mark.asyncio
    async def test_token_generation_exception(self, user_factory, login_helper):
        await user_factory(
            {
                "user_email": "tokengen@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "TokenGen",
                "user_country_code": "GB",
            }
        )
        with patch("app.api.v1.auth.create_token", side_effect=Exception("fail")):
            resp = await login_helper("tokengen@example.com", "SecurePass123!")
            assert resp.status_code == 500


class TestTokenRefresh:
    @pytest.mark.asyncio
    async def test_refresh_success(self, user_factory, login_helper, client):
        await user_factory(
            {
                "user_email": "refresh@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "Ref",
                "user_country_code": "GB",
            }
        )
        login = await login_helper("refresh@example.com", "SecurePass123!")
        refresh_token = login.json()["refresh_token"]
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": refresh_token}
        )
        assert resp.status_code == 200
        new = resp.json()
        assert {"access_token", "refresh_token"} <= new.keys()
        assert new["refresh_token"] != refresh_token

    @pytest.mark.asyncio
    async def test_refresh_with_access_token(self, user_factory, login_helper, client):
        await user_factory(
            {
                "user_email": "wrongtype@example.com",
                "user_password": "SecurePass123!",
                "user_first_name": "WrongType",
                "user_country_code": "GB",
            }
        )
        login = await login_helper("wrongtype@example.com", "SecurePass123!")
        access_token = login.json()["access_token"]
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": access_token}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_refresh_invalid_token(self, client):
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "not.a.jwt"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_decode_missing_type(self, client, mocker):
        mock_decode = mocker.patch("app.api.v1.auth.decode_token")
        mock_decode.return_value = {"sub": "user"}
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "tok"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_decode_missing_sub(self, client, mocker):
        mock_decode = mocker.patch("app.api.v1.auth.decode_token")
        mock_decode.return_value = {"type": "refresh"}
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "tok"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_validate_user_exists_raises(self, client, mocker):
        mocker.patch(
            "app.api.v1.auth.decode_token", return_value={"type": "refresh", "sub": "u"}
        )
        val = mocker.patch("app.api.v1.auth.validate_user_exists")
        val.side_effect = BaseApplicationError("fail", "FAIL_CODE")
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "tok"}
        )
        assert resp.status_code == 400

    @pytest.mark.asyncio
    async def test_invalid_payload_type(self, client, mocker):
        mocker.patch("app.api.v1.auth.decode_token", return_value={"sub": "u"})
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "tok"}
        )
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_decode_exception(self, client, mocker):
        mocker.patch("app.api.v1.auth.decode_token", side_effect=Exception("decode"))
        resp = await client.post(
            f"{PREFIX}/auth/token/refresh", json={"refresh_token": "tok"}
        )
        assert resp.status_code == 401


class TestAuthErrorHandling:
    @pytest.mark.asyncio
    async def test_authenticate_none(self, login_helper, mocker):
        mocker.patch("app.api.v1.auth.authenticate_user", return_value=None)
        resp = await login_helper("invalid@example.com", "ValidPass123!")
        assert resp.status_code == 401

    @pytest.mark.asyncio
    async def test_auth_general_exception(self, login_helper, mocker):
        mocker.patch("app.api.v1.auth.authenticate_user", side_effect=Exception("db"))
        resp = await login_helper("err2@example.com", "ValidPass123!")
        assert resp.status_code == 500
