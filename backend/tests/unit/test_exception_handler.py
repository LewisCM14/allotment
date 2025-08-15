"""
Tests for exception handler middleware - refactored to use conftest.py fixtures
"""

import json
import uuid

import pytest
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse

from app.api.middleware.error_codes import (
    GENERAL_BUSINESS_RULE_VIOLATION,
    GENERAL_UNEXPECTED_ERROR,
    GENERAL_VALIDATION_ERROR,
    RESOURCE_INVALID_STATE,
)
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    DatabaseIntegrityError,
    EmailAlreadyRegisteredError,
    ExceptionHandlingMiddleware,
    InvalidResourceStateError,
    InvalidTokenError,
    UserNotFoundError,
    application_exception_handler,
    create_error_response,
    general_exception_handler,
    handle_auth_exceptions,
    handle_db_exceptions,
    http_exception_handler,
    validate_user_exists,
    validation_exception_handler,
)


@pytest.fixture
def dummy_request():
    """Fixture for creating a dummy request object."""

    class DummyRequest:
        def __init__(self, headers=None, method="GET", url_path="/dummy"):
            self.headers = headers or {}
            self.method = method
            self.url = type("URL", (), {"path": url_path})

    return DummyRequest


@pytest.fixture
def test_request_id():
    """Fixture for consistent request ID in tests."""
    return str(uuid.uuid4())


class TestCreateErrorResponse:
    """Test error response creation utilities."""

    def test_server_error_metadata(self, test_request_id):
        """Test server error response includes all required metadata."""
        resp = create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected failure",
            error_type="server_error",
            error_code=GENERAL_UNEXPECTED_ERROR,
            request_id=test_request_id,
        )

        body = resp.body.decode("utf-8")
        data = json.loads(body)
        detail = data["detail"][0]

        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert detail["msg"] == "Unexpected failure"
        assert detail["type"] == "server_error"
        assert detail["code"] == GENERAL_UNEXPECTED_ERROR
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail

    def test_create_error_response_with_extra_data(self, test_request_id):
        """Test error response with additional data."""
        extra = {"extra": "value"}
        resp = create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Server failure",
            error_type="server_error",
            error_code=GENERAL_UNEXPECTED_ERROR,
            request_id=test_request_id,
            extra_data=extra,
        )

        body = resp.body.decode("utf-8")
        data = json.loads(body)
        detail = data["detail"][0]

        assert detail["msg"] == "Server failure"
        assert detail["extra"] == "value"
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail


class TestValidationExceptionHandler:
    """Test validation exception handling."""

    @pytest.fixture
    def validation_request(self, dummy_request):
        """Request fixture for validation tests."""
        return dummy_request(headers={"X-Request-ID": "test-req-id"})

    @pytest.fixture
    def validation_errors(self):
        """Standard validation error data."""
        return [
            {
                "msg": "Field missing",
                "loc": ["body", "field"],
                "type": "value_error.missing",
                "ctx": {},
            }
        ]

    async def test_validation_exception_handler(
        self, validation_request, validation_errors
    ):
        """Test validation exception returns proper error format."""
        exc = RequestValidationError(validation_errors)
        resp = await validation_exception_handler(validation_request, exc)
        body = json.loads(resp.body.decode("utf-8"))

        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert body["detail"][0]["msg"] == "Field missing"
        assert body["detail"][0]["code"] == GENERAL_VALIDATION_ERROR


class TestHTTPExceptionHandler:
    """Test HTTP exception handling."""

    @pytest.fixture
    def http_request(self, dummy_request):
        """Request fixture for HTTP tests."""
        return dummy_request(headers={"X-Request-ID": "http-req"})

    async def test_http_exception_handler(self, http_request):
        """Test HTTP exception returns proper error format."""
        exc = HTTPException(status_code=404, detail="Not found")
        resp = await http_exception_handler(http_request, exc)
        body = json.loads(resp.body.decode("utf-8"))

        assert resp.status_code == 404
        assert body["detail"][0]["msg"] == "Not found"
        assert body["detail"][0]["code"] == "HTTP_404"


class TestApplicationExceptionHandler:
    """Test application exception handling."""

    @pytest.fixture
    def app_request(self, dummy_request):
        """Request fixture for application tests."""
        return dummy_request(headers={"X-Request-ID": "app-req"})

    async def test_application_exception_handler(self, app_request):
        """Test application exception returns proper error format."""
        error = BusinessLogicError(message="Business failure")
        resp = await application_exception_handler(app_request, error)
        body = json.loads(resp.body.decode("utf-8"))

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert body["detail"][0]["msg"] == "Business failure"
        assert body["detail"][0]["code"] == GENERAL_BUSINESS_RULE_VIOLATION


class TestGeneralExceptionHandler:
    """Test general exception handling."""

    @pytest.fixture
    def general_request(self, dummy_request):
        """Request fixture for general tests."""
        return dummy_request(headers={"X-Request-ID": "gen-req"})

    async def test_general_exception_handler(self, general_request):
        """Test general exception returns sanitized error."""
        error = Exception("Unexpected error")
        resp = await general_exception_handler(general_request, error)
        body = json.loads(resp.body.decode("utf-8"))

        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert body["detail"][0]["msg"] == "An unexpected error occurred"
        assert body["detail"][0]["code"] == GENERAL_UNEXPECTED_ERROR


class TestExceptionHandlingMiddleware:
    """Test exception handling middleware."""

    @pytest.fixture
    def middleware_request(self, dummy_request):
        """Request fixture for middleware tests."""
        return dummy_request(headers={"X-Request-ID": "mid-req"})

    @pytest.fixture
    def success_call_next(self):
        """Fixture for successful call_next handler."""

        async def call_next(req):
            return JSONResponse(status_code=200, content={"msg": "ok"})

        return call_next

    @pytest.fixture
    def failure_call_next(self):
        """Fixture for failing call_next handler."""

        async def call_next(req):
            raise BusinessLogicError(message="Middleware failure")

        return call_next

    async def test_middleware_success(self, middleware_request, success_call_next):
        """Test middleware allows successful requests through."""
        middleware = ExceptionHandlingMiddleware(None)
        resp = await middleware.dispatch(middleware_request, success_call_next)
        assert resp.status_code == 200

    async def test_middleware_fail(self, middleware_request, failure_call_next):
        """Test middleware catches and formats exceptions."""
        middleware = ExceptionHandlingMiddleware(None)
        resp = await middleware.dispatch(middleware_request, failure_call_next)
        body = json.loads(resp.body.decode("utf-8"))

        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert body["detail"][0]["msg"] == "Middleware failure"


class TestHandleDbExceptions:
    """Test database exception handling utilities."""

    @pytest.fixture
    def integrity_error_email(self):
        """Fixture for email constraint violation."""
        from sqlalchemy.exc import IntegrityError

        return IntegrityError("unique constraint failed: email", None, None)

    @pytest.fixture
    def integrity_error_allotment(self):
        """Fixture for allotment constraint violation."""
        from sqlalchemy.exc import IntegrityError

        return IntegrityError(
            "unique constraint failed: user_allotment.user_id", None, None
        )

    @pytest.fixture
    def general_integrity_error(self):
        """Fixture for general integrity violation."""
        from sqlalchemy.exc import IntegrityError

        return IntegrityError("other integrity", None, None)

    @pytest.fixture
    def sqlalchemy_error(self):
        """Fixture for general SQLAlchemy error."""
        from sqlalchemy.exc import SQLAlchemyError

        return SQLAlchemyError("sqlalchemy error")

    def test_handle_db_exceptions_unique_email(self, integrity_error_email):
        """Test email constraint violation handling."""
        with pytest.raises(EmailAlreadyRegisteredError):
            handle_db_exceptions(integrity_error_email)

    def test_handle_db_exceptions_unique_allotment(self, integrity_error_allotment):
        """Test allotment constraint violation handling."""
        with pytest.raises(DatabaseIntegrityError):
            handle_db_exceptions(integrity_error_allotment)

    def test_handle_db_exceptions_other_integrity(self, general_integrity_error):
        """Test general integrity violation handling."""
        with pytest.raises(DatabaseIntegrityError):
            handle_db_exceptions(general_integrity_error)

    def test_handle_db_exceptions_sqlalchemy(self, sqlalchemy_error):
        """Test general SQLAlchemy error handling."""
        with pytest.raises(BusinessLogicError):
            handle_db_exceptions(sqlalchemy_error)


class TestHandleAuthExceptions:
    """Test authentication exception handling utilities."""

    @pytest.fixture
    def auth_value_error(self):
        """Fixture for authentication-related ValueError."""
        return ValueError("key may not be safe")

    def test_handle_auth_exceptions_valueerror(self, auth_value_error):
        """Test authentication ValueError handling."""
        with pytest.raises(InvalidTokenError):
            handle_auth_exceptions(auth_value_error)


class TestValidateUserExists:
    """Test user validation utilities."""

    async def test_validate_user_exists_email(self, mocker):
        """Test user validation by email when user not found."""
        db = mocker.AsyncMock()
        user_model = mocker.Mock()
        mock_query = mocker.Mock()
        db.execute = mocker.AsyncMock()
        db.execute.return_value.scalar_one_or_none = mocker.Mock(return_value=None)

        import app.api.middleware.exception_handler as eh

        mocker.patch.object(eh, "select", return_value=mock_query)

        with pytest.raises(UserNotFoundError):
            await validate_user_exists(db, user_model, user_email="x@example.com")

    async def test_validate_user_exists_user_id(self, mocker):
        """Test user validation by ID when user exists."""
        db = mocker.AsyncMock()
        user_model = mocker.Mock()
        mock_query = mocker.Mock()
        db.execute.return_value.scalar_one_or_none = mocker.Mock(return_value="user")

        import app.api.middleware.exception_handler as eh

        mocker.patch.object(eh, "select", return_value=mock_query)

        result = await validate_user_exists(db, user_model, user_id=str(uuid.uuid4()))
        assert result == "user"

    async def test_validate_user_exists_value_error(self, mocker):
        """Test user validation with invalid UUID."""
        db = mocker.AsyncMock()
        user_model = mocker.Mock()
        db.execute.side_effect = ValueError("invalid literal for uuid")

        import app.api.middleware.exception_handler as eh

        mocker.patch.object(
            eh,
            "select",
            side_effect=lambda *a, **kw: (_ for _ in ()).throw(
                ValueError("invalid literal for uuid")
            ),
        )

        with pytest.raises(InvalidTokenError):
            await validate_user_exists(db, user_model, user_id="not-a-uuid")

    def test_invalid_resource_state_error(self):
        """Test InvalidResourceStateError properties."""
        exc = InvalidResourceStateError("Invalid state")
        assert exc.message == "Invalid state"
        assert exc.error_code == RESOURCE_INVALID_STATE
        assert exc.status_code == status.HTTP_409_CONFLICT
