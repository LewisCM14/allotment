# ------------------------------
# Unit tests for pydantic_validation_exception_handler
# ------------------------------
import json

import pytest
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ValidationError
from sqlalchemy.exc import IntegrityError, SQLAlchemyError

from app.api.middleware.exceptions import (
    BusinessLogicError,
    ExpiredTokenError,
    InvalidTokenError,
    handle_auth_exceptions,
    handle_db_exceptions,
    pydantic_validation_exception_handler,
)
from app.api.middleware.logging_middleware import SENSITIVE_FIELDS


# Dummy request for async handlers
class FakeRequest:
    def __init__(self, headers=None, method="GET", url_path="/test"):
        self.headers = headers or {}
        self.method = method
        self.url = type("URL", (), {"path": url_path})


# Dummy model for generating ValidationError
class DummyModel(BaseModel):
    pass

    @pytest.mark.asyncio
    async def test_handler_sanitizes_sensitive_fields(self):
        # Pydantic v2: construct ValidationError using from_exception_data
        errors = [
            {
                "type": "value_error",
                "loc": ("body", "password"),
                "msg": "Invalid input",
                "input": "bad",
                "ctx": {
                    "password": "secret_value",
                    "other": "ok",
                    "error": "Invalid input",
                },
            }
        ]
        exc = ValidationError.from_exception_data(DummyModel, errors)
        req = FakeRequest(headers={"X-Request-ID": "pydantic-test"})
        # Call the handler
        response: JSONResponse = await pydantic_validation_exception_handler(req, exc)
        body = json.loads(response.body.decode("utf-8"))
        detail = body["detail"][0]
        # Expect sensitive field redacted based on SENSITIVE_FIELDS
        expected_ctx = {}
        for key, value in errors[0]["ctx"].items():
            expected_ctx[key] = (
                "[REDACTED]" if key.lower() in SENSITIVE_FIELDS else value
            )
        # Pydantic v2 error message is now 'Value error, Invalid input'
        assert detail["msg"] == "Value error, Invalid input"
        assert detail["loc"] == ["body", "password"]
        assert detail["type"] == "value_error"
        assert detail["code"]  # code is set to a non-empty value
        assert detail["ctx"] == expected_ctx


# ------------------------------
# Unit tests for handle_db_exceptions
# ------------------------------
class TestDBExceptions:
    def test_email_constraint_raises_email_registered(self):
        # Test IntegrityError with unique constraint on email.
        error_message = "unique constraint failed: email"
        exc = IntegrityError(error_message, None, None)
        with pytest.raises(Exception) as exc_info:
            handle_db_exceptions(exc)
        # Expect EmailAlreadyRegisteredError should be raised
        assert "email" in str(exc_info.value).lower()

    def test_user_allotment_constraint(self):
        # Test IntegrityError with unique constraint on user_allotment.user_id.
        error_message = "unique constraint failed: user_allotment.user_id"
        exc = IntegrityError(error_message, None, None)
        with pytest.raises(Exception) as exc_info:
            handle_db_exceptions(exc)
        # Expect message provided by handler for user allotment case.
        assert "user already has an allotment" in str(exc_info.value).lower()

    def test_generic_integrity_error(self):
        # IntegrityError that does not match the two special cases.
        error_message = "some other integrity error"
        exc = IntegrityError(error_message, None, None)
        with pytest.raises(Exception) as exc_info:
            handle_db_exceptions(exc)
        # Expect a DatabaseIntegrityError is raised with generic message.
        assert "data integrity violation" in str(exc_info.value).lower()

    def test_sqlalchemy_error_raises_business_logic(self):
        # Test SQLAlchemyError branch.
        class FakeSQLAlchemyError(SQLAlchemyError):
            pass

        exc = FakeSQLAlchemyError("sqlalchemy error occurred")
        with pytest.raises(BusinessLogicError) as exc_info:
            handle_db_exceptions(exc)
        # Expect the BusinessLogicError with specific message.
        assert "database operation failed" in str(exc_info.value).lower()


# ------------------------------
# Unit tests for handle_auth_exceptions
# ------------------------------
class TestAuthExceptions:
    def test_expired_token_raises_expired_token_error(self, monkeypatch):
        import sys
        import types

        class FakeAuthlibExpiredTokenError(Exception):
            pass

        fake_errors_mod = types.SimpleNamespace(
            ExpiredTokenError=FakeAuthlibExpiredTokenError,
            InvalidClaimError=type("Other", (Exception,), {}),
            JoseError=type("Other2", (Exception,), {}),
        )
        sys.modules["authlib.jose.errors"] = fake_errors_mod
        exc = FakeAuthlibExpiredTokenError("expired")
        with pytest.raises(ExpiredTokenError):
            handle_auth_exceptions(exc)

    def test_invalid_claim_raises_invalid_token_error(self, monkeypatch):
        import sys
        import types

        class FakeInvalidClaimError(Exception):
            pass

        fake_errors_mod = types.SimpleNamespace(
            ExpiredTokenError=type("Other", (Exception,), {}),
            InvalidClaimError=FakeInvalidClaimError,
            JoseError=type("Other2", (Exception,), {}),
        )
        sys.modules["authlib.jose.errors"] = fake_errors_mod
        exc = FakeInvalidClaimError("invalid claim")
        with pytest.raises(InvalidTokenError) as exc_info:
            handle_auth_exceptions(exc)
        # Accept any message, just check the type
        assert isinstance(exc_info.value, InvalidTokenError)

    def test_jose_error_raises_invalid_token_error(self, monkeypatch):
        import sys
        import types

        class FakeJoseError(Exception):
            pass

        fake_errors_mod = types.SimpleNamespace(
            ExpiredTokenError=type("Other", (Exception,), {}),
            InvalidClaimError=type("Other2", (Exception,), {}),
            JoseError=FakeJoseError,
        )
        sys.modules["authlib.jose.errors"] = fake_errors_mod
        exc = FakeJoseError("jose error")
        with pytest.raises(InvalidTokenError) as exc_info:
            handle_auth_exceptions(exc)
        assert isinstance(exc_info.value, InvalidTokenError)

    def test_value_error_invalid_key_raises_invalid_token_error(self):
        exc = ValueError("Invalid key provided")
        with pytest.raises(InvalidTokenError) as exc_info:
            handle_auth_exceptions(exc)
        assert isinstance(exc_info.value, InvalidTokenError)

    def test_value_error_no_match_does_nothing(self):
        # A ValueError that does not match the specific phrases will not be caught
        exc = ValueError("some other value error")
        # In this branch nothing is raised, so function should simply complete (do nothing)
        # Hence, we simply call it and expect no exception.
        try:
            handle_auth_exceptions(exc)
        except Exception as e:
            pytest.fail(f"Unexpected exception raised: {e}")


import uuid

import pytest
from fastapi import HTTPException, status
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel

from app.api.middleware.error_codes import (
    GENERAL_BUSINESS_RULE_VIOLATION,
    GENERAL_UNEXPECTED_ERROR,
    GENERAL_VALIDATION_ERROR,
    RESOURCE_INVALID_STATE,
)
from app.api.middleware.exceptions import (
    BaseApplicationError,
    ExceptionHandlingMiddleware,
    InvalidResourceStateError,
    application_exception_handler,
    create_error_response,
    general_exception_handler,
    http_exception_handler,
    validation_exception_handler,
)


class DummyRequest:
    def __init__(self, headers=None, method="GET", url_path="/dummy"):
        self.headers = headers or {}
        self.method = method
        self.url = type("URL", (), {"path": url_path})


# ------------------------------
# Tests for create_error_response
# ------------------------------
class TestCreateErrorResponse:
    def test_server_error_metadata(self):
        req_id = str(uuid.uuid4())
        resp = create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Unexpected failure",
            error_type="server_error",
            error_code=GENERAL_UNEXPECTED_ERROR,
            request_id=req_id,
        )
        body = resp.body.decode("utf-8")
        data = json.loads(body)
        detail = data["detail"][0]
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert detail["msg"] == "Unexpected failure"
        assert detail["type"] == "server_error"
        assert detail["code"] == GENERAL_UNEXPECTED_ERROR
        # Check metadata fields added for server errors
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail

    def test_create_error_response_with_extra_data(self):
        import json

        from fastapi import status

        from app.api.middleware.error_codes import GENERAL_UNEXPECTED_ERROR
        from app.api.middleware.exceptions import create_error_response

        extra = {"extra": "value"}
        req_id = "test-req-extra"
        resp = create_error_response(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            message="Server failure",
            error_type="server_error",
            error_code=GENERAL_UNEXPECTED_ERROR,
            request_id=req_id,
            extra_data=extra,
        )
        body = resp.body.decode("utf-8")
        data = json.loads(body)
        detail = data["detail"][0]
        assert detail["msg"] == "Server failure"
        assert detail["extra"] == "value"
        # Verify metadata is added for server errors
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail


# ------------------------------
# Tests for validation_exception_handler
# ------------------------------
class TestValidationExceptionHandler:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "test-req-id"})

    @pytest.mark.asyncio
    async def test_validation_exception_handler(self, dummy_req):
        errors = [
            {
                "msg": "Field missing",
                "loc": ["body", "field"],
                "type": "value_error.missing",
                "ctx": {},
            }
        ]
        exc = RequestValidationError(errors)
        resp = await validation_exception_handler(dummy_req, exc)
        body = json.loads(resp.body.decode("utf-8"))
        assert resp.status_code == status.HTTP_422_UNPROCESSABLE_ENTITY
        assert body["detail"][0]["msg"] == "Field missing"
        assert body["detail"][0]["code"] == GENERAL_VALIDATION_ERROR

    @pytest.mark.asyncio
    async def test_validation_exception_handler_with_ctx(self, dummy_req):
        errors = [
            {
                "msg": "Invalid input",
                "loc": ["body", "password"],
                "type": "value_error",
                "ctx": {"password": "hunter2", "info": "extra"},
            }
        ]
        exc = RequestValidationError(errors)
        resp = await validation_exception_handler(dummy_req, exc)
        body = json.loads(resp.body.decode("utf-8"))
        detail = body["detail"][0]
        assert detail["msg"] == "Invalid input"
        assert detail["loc"] == ["body", "password"]
        assert detail["type"] == "validation_error"
        # The handler always outputs an empty dict for ctx per its implementation
        assert detail["ctx"] == {}

    @pytest.mark.asyncio
    async def test_validation_exception_handler_with_nonserializable_ctx(
        self, dummy_req
    ):
        # Using a lambda (non-serializable) in ctx to force the exception branch.
        errors = [
            {
                "msg": "Non-serializable ctx",
                "loc": ["query", "field"],
                "type": "value_error",
                "ctx": {"key": lambda x: x},
            }
        ]
        exc = RequestValidationError(errors)
        resp = await validation_exception_handler(dummy_req, exc)
        body = json.loads(resp.body.decode("utf-8"))
        detail = body["detail"][0]
        assert detail["msg"] == "Non-serializable ctx"
        # The handler sets ctx to empty dict regardless of input.
        assert detail["ctx"] == {}


# ------------------------------
# Tests for http_exception_handler
# ------------------------------
class TestHTTPExceptionHandler:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "http-req"})

    @pytest.mark.asyncio
    async def test_http_exception_handler(self, dummy_req):
        exc = HTTPException(status_code=404, detail="Not found")
        resp = await http_exception_handler(dummy_req, exc)
        body = json.loads(resp.body.decode("utf-8"))
        assert resp.status_code == 404
        assert body["detail"][0]["msg"] == "Not found"
        assert body["detail"][0]["code"] == "HTTP_404"


# ------------------------------
# Tests for application_exception_handler
# ------------------------------
class DummyAppError(BaseApplicationError):
    pass


class TestApplicationExceptionHandler:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "app-req"})

    @pytest.mark.asyncio
    async def test_application_exception_handler(self, dummy_req):
        error = BusinessLogicError(message="Business failure")
        resp = await application_exception_handler(dummy_req, error)
        body = json.loads(resp.body.decode("utf-8"))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert body["detail"][0]["msg"] == "Business failure"
        assert body["detail"][0]["code"] == GENERAL_BUSINESS_RULE_VIOLATION


# ------------------------------
# Tests for general_exception_handler
# ------------------------------
class TestGeneralExceptionHandler:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "gen-req"})

    @pytest.mark.asyncio
    async def test_general_exception_handler(self, dummy_req):
        error = Exception("Unexpected error")
        resp = await general_exception_handler(dummy_req, error)
        body = json.loads(resp.body.decode("utf-8"))
        assert resp.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        assert body["detail"][0]["msg"] == "An unexpected error occurred"
        assert body["detail"][0]["code"] == GENERAL_UNEXPECTED_ERROR


# ------------------------------
# Tests for ExceptionHandlingMiddleware
# ------------------------------
class TestExceptionHandlingMiddleware:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "mid-req"})

    async def dummy_call_next_success(self, req):
        # ...existing code...
        return JSONResponse(status_code=200, content={"msg": "ok"})

    async def dummy_call_next_fail(self, req):
        raise BusinessLogicError(message="Middleware failure")

    @pytest.mark.asyncio
    async def test_middleware_success(self, dummy_req):
        middleware = ExceptionHandlingMiddleware(None)
        resp = await middleware.dispatch(dummy_req, self.dummy_call_next_success)
        assert resp.status_code == 200

    @pytest.mark.asyncio
    async def test_middleware_fail(self, dummy_req):
        middleware = ExceptionHandlingMiddleware(None)
        resp = await middleware.dispatch(dummy_req, self.dummy_call_next_fail)
        body = json.loads(resp.body.decode("utf-8"))
        assert resp.status_code == status.HTTP_400_BAD_REQUEST
        assert body["detail"][0]["msg"] == "Middleware failure"


def test_invalid_resource_state_error():
    from fastapi import status

    exc = InvalidResourceStateError("Invalid state")
    assert exc.message == "Invalid state"
    assert exc.error_code == RESOURCE_INVALID_STATE
    assert exc.status_code == status.HTTP_409_CONFLICT
