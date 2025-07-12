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


class DummyRequest:
    def __init__(self, headers=None, method="GET", url_path="/dummy"):
        self.headers = headers or {}
        self.method = method
        self.url = type("URL", (), {"path": url_path})


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
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail

    def test_create_error_response_with_extra_data(self):
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
        assert "request_id" in detail
        assert "timestamp" in detail
        assert "environment" in detail


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


class TestExceptionHandlingMiddleware:
    @pytest.fixture
    def dummy_req(self):
        return DummyRequest(headers={"X-Request-ID": "mid-req"})

    async def dummy_call_next_success(self, req):
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


class TestHandleDbExceptions:
    def test_handle_db_exceptions_unique_email(self):
        from sqlalchemy.exc import IntegrityError

        err = IntegrityError("unique constraint failed: email", None, None)
        with pytest.raises(EmailAlreadyRegisteredError):
            handle_db_exceptions(err)

    def test_handle_db_exceptions_unique_allotment(self):
        from sqlalchemy.exc import IntegrityError

        err = IntegrityError(
            "unique constraint failed: user_allotment.user_id", None, None
        )
        with pytest.raises(DatabaseIntegrityError):
            handle_db_exceptions(err)

    def test_handle_db_exceptions_other_integrity(self):
        from sqlalchemy.exc import IntegrityError

        err = IntegrityError("other integrity", None, None)
        with pytest.raises(DatabaseIntegrityError):
            handle_db_exceptions(err)

    def test_handle_db_exceptions_sqlalchemy(self):
        from sqlalchemy.exc import SQLAlchemyError

        err = SQLAlchemyError("sqlalchemy error")
        with pytest.raises(BusinessLogicError):
            handle_db_exceptions(err)


class TestHandleAuthExceptions:
    def test_handle_auth_exceptions_valueerror(self):
        err = ValueError("key may not be safe")
        with pytest.raises(InvalidTokenError):
            handle_auth_exceptions(err)


class TestValidateUserExists:
    @pytest.mark.asyncio
    async def test_validate_user_exists_email(self, mocker):
        # Patch select to avoid SQLAlchemy ArgumentError
        db = mocker.AsyncMock()
        user_model = mocker.Mock()
        mock_query = mocker.Mock()
        db.execute = mocker.AsyncMock()
        db.execute.return_value.scalar_one_or_none = mocker.Mock(return_value=None)
        # Patch select to return mock_query
        import app.api.middleware.exception_handler as eh

        mocker.patch.object(eh, "select", return_value=mock_query)
        with pytest.raises(UserNotFoundError):
            await validate_user_exists(db, user_model, user_email="x@example.com")

    @pytest.mark.asyncio
    async def test_validate_user_exists_user_id(self, mocker):
        db = mocker.AsyncMock()
        user_model = mocker.Mock()
        mock_query = mocker.Mock()
        db.execute.return_value.scalar_one_or_none = mocker.Mock(return_value="user")
        import app.api.middleware.exception_handler as eh

        mocker.patch.object(eh, "select", return_value=mock_query)
        result = await validate_user_exists(db, user_model, user_id=str(uuid.uuid4()))
        assert result == "user"

    @pytest.mark.asyncio
    async def test_validate_user_exists_value_error(self, mocker):
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
        exc = InvalidResourceStateError("Invalid state")
        assert exc.message == "Invalid state"
        assert exc.error_code == RESOURCE_INVALID_STATE
        assert exc.status_code == status.HTTP_409_CONFLICT
