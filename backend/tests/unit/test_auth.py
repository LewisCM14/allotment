import types
from unittest.mock import MagicMock

import bcrypt
import pytest
from fastapi import HTTPException

from app.api.core import auth_utils
from app.api.middleware.exception_handler import (
    AuthenticationError,
    BaseApplicationError,
    InvalidTokenError,
)
from app.api.schemas import TokenResponse
from app.api.schemas.user.user_schema import RefreshRequest, UserLogin
from app.api.v1 import auth
from tests.test_helpers import validate_token_response_schema


class TestAuthUtilsCoverage:
    def test_create_token_missing_private_key(self, monkeypatch):
        monkeypatch.setattr(auth_utils.settings, "PRIVATE_KEY", None)
        with pytest.raises(ValueError, match="Private key is not loaded"):
            auth_utils.create_token("user-id")

    def test_create_token_unknown_type(self, monkeypatch):
        monkeypatch.setattr(auth_utils.settings, "PRIVATE_KEY", "key")
        with pytest.raises(ValueError, match="Unknown token type"):
            auth_utils.create_token("user-id", token_type="badtype")

    def test_create_token_exception_logging(self, monkeypatch):
        monkeypatch.setattr(auth_utils.settings, "PRIVATE_KEY", "key")
        monkeypatch.setattr(auth_utils.settings, "JWT_ALGORITHM", "alg")
        # Patch jwt.encode to raise
        monkeypatch.setattr(
            auth_utils.jwt,
            "encode",
            lambda *a, **k: (_ for _ in ()).throw(Exception("fail")),
        )
        with pytest.raises(Exception, match="fail"):
            auth_utils.create_token("user-id")

    def test_verify_password_success(self):
        pw = "pw"
        hashed = bcrypt.hashpw(pw.encode(), bcrypt.gensalt()).decode()
        assert auth_utils.verify_password(pw, hashed)

    def test_verify_password_failure(self):
        pw = "pw"
        hashed = bcrypt.hashpw(b"other", bcrypt.gensalt()).decode()
        assert not auth_utils.verify_password(pw, hashed)

    def test_verify_password_exception(self, monkeypatch):
        monkeypatch.setattr(
            bcrypt, "checkpw", lambda *a, **k: (_ for _ in ()).throw(Exception("fail"))
        )
        assert not auth_utils.verify_password("pw", "hash")

    def test_decode_token_success(self, monkeypatch):
        monkeypatch.setattr(auth_utils.settings, "PUBLIC_KEY", "pub")
        monkeypatch.setattr(auth_utils.jwt, "decode", lambda t, k: {"sub": "u"})
        assert auth_utils.decode_token("tok") == {"sub": "u"}

    def test_decode_token_invalid(self, monkeypatch):
        monkeypatch.setattr(auth_utils.settings, "PUBLIC_KEY", "pub")
        monkeypatch.setattr(
            auth_utils.jwt,
            "decode",
            lambda t, k: (_ for _ in ()).throw(auth_utils.JoseError("fail")),
        )
        with pytest.raises(auth_utils.InvalidTokenError):
            auth_utils.decode_token("tok")

    @pytest.mark.asyncio
    async def test_authenticate_user_success(self, mocker):
        db = MagicMock()
        user = MagicMock()
        user.user_password_hash = bcrypt.hashpw(b"pw", bcrypt.gensalt()).decode()
        db.execute = mocker.AsyncMock(
            return_value=types.SimpleNamespace(scalar_one_or_none=lambda: user)
        )
        mocker.patch("app.api.core.auth_utils.verify_password", return_value=True)
        db.commit = mocker.AsyncMock()
        db.refresh = mocker.AsyncMock()
        result = await auth_utils.authenticate_user(db, "e", "pw")
        assert result == user

    @pytest.mark.asyncio
    async def test_authenticate_user_not_found(self, mocker):
        db = MagicMock()
        db.execute = mocker.AsyncMock(
            return_value=types.SimpleNamespace(scalar_one_or_none=lambda: None)
        )
        result = await auth_utils.authenticate_user(db, "e", "pw")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_password_mismatch(self, mocker):
        db = MagicMock()
        user = MagicMock()
        user.user_password_hash = "hash"
        db.execute = mocker.AsyncMock(
            return_value=types.SimpleNamespace(scalar_one_or_none=lambda: user)
        )
        mocker.patch("app.api.core.auth_utils.verify_password", return_value=False)
        result = await auth_utils.authenticate_user(db, "e", "pw")
        assert result is None

    @pytest.mark.asyncio
    async def test_authenticate_user_exception(self, mocker):
        db = MagicMock()
        db.execute = mocker.AsyncMock(side_effect=Exception("fail"))
        result = await auth_utils.authenticate_user(db, "e", "pw")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_current_user_missing_header(self, mocker):
        with pytest.raises(HTTPException) as e:
            await auth_utils.get_current_user(authorization=None, db=MagicMock())
        assert e.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_token_type(self, mocker):
        with pytest.raises(HTTPException) as e:
            await auth_utils.get_current_user(
                authorization="Basic token", db=MagicMock()
            )
        assert e.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_missing_token(self, mocker):
        with pytest.raises(HTTPException) as e:
            await auth_utils.get_current_user(authorization="Bearer ", db=MagicMock())
        assert e.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_invalid_payload(self, mocker):
        mocker.patch("app.api.core.auth_utils.decode_token", return_value={})
        with pytest.raises(HTTPException) as e:
            await auth_utils.get_current_user(
                authorization="Bearer tok", db=MagicMock()
            )
        assert e.value.status_code == 401

    @pytest.mark.asyncio
    async def test_get_current_user_user_not_found(self, mocker):
        mocker.patch("app.api.core.auth_utils.decode_token", return_value={"sub": "u"})
        mocker.patch(
            "app.api.core.auth_utils.validate_user_exists",
            side_effect=HTTPException(status_code=401, detail="not found"),
        )
        with pytest.raises(HTTPException) as e:
            await auth_utils.get_current_user(
                authorization="Bearer tok", db=MagicMock()
            )
        assert e.value.status_code == 401


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
