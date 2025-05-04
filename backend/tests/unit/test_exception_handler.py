import json
from unittest.mock import MagicMock

import pytest
from fastapi import status

from app.api.core.config import settings
from app.api.middleware.error_codes import (
    DB_INTEGRITY_ERROR,
    GENERAL_BUSINESS_RULE_VIOLATION,
    USER_NOT_FOUND,
)
from app.api.middleware.exception_handler import (
    BaseApplicationError,
    BusinessLogicError,
    DatabaseIntegrityError,
    ExceptionHandlingMiddleware,
    UserNotFoundError,
)


class TestBaseApplicationError:
    def test_base_application_error(self):
        """Test BaseApplicationError attributes."""
        error = BaseApplicationError(
            message="Test error",
            error_code="TEST_001",
            status_code=status.HTTP_400_BAD_REQUEST,
        )
        assert error.message == "Test error"
        assert error.error_code == "TEST_001"
        assert error.status_code == status.HTTP_400_BAD_REQUEST


class TestCustomExceptions:
    def test_business_logic_error(self):
        """Test BusinessLogicError attributes."""
        error = BusinessLogicError()
        assert error.message == "Business logic error"
        assert error.error_code == GENERAL_BUSINESS_RULE_VIOLATION
        assert error.status_code == status.HTTP_400_BAD_REQUEST

    def test_user_not_found_error(self):
        """Test UserNotFoundError attributes."""
        error = UserNotFoundError()
        assert error.message == "User not found"
        assert error.error_code == USER_NOT_FOUND
        assert error.status_code == status.HTTP_404_NOT_FOUND

    def test_database_integrity_error(self):
        """Test DatabaseIntegrityError attributes."""
        error = DatabaseIntegrityError()
        assert error.message == "Database integrity constraint violation"
        assert error.error_code == DB_INTEGRITY_ERROR
        assert error.status_code == status.HTTP_409_CONFLICT


@pytest.mark.asyncio
async def test_exception_handling_middleware_handles_base_application_error():
    """Test that the middleware handles BaseApplicationError correctly."""
    middleware = ExceptionHandlingMiddleware(None)

    async def mock_call_next(_):
        raise BusinessLogicError(message="Test business logic error")

    mock_request = MagicMock()
    mock_request.headers = {"X-Request-ID": "test-request-id"}
    mock_request.url.path = "/test-path"
    mock_request.method = "GET"

    response = await middleware.dispatch(mock_request, mock_call_next)

    assert response.status_code == status.HTTP_400_BAD_REQUEST
    response_body = json.loads(response.body.decode("utf-8"))
    assert response_body == {
        "detail": [
            {
                "msg": "Test business logic error",
                "type": "businesslogicerror",
                "code": GENERAL_BUSINESS_RULE_VIOLATION,
            }
        ]
    }


@pytest.mark.asyncio
async def test_exception_handling_middleware_handles_unhandled_exception():
    """Test that the middleware handles unhandled exceptions correctly."""
    middleware = ExceptionHandlingMiddleware(None)

    async def mock_call_next(_):
        raise ValueError("Test unhandled exception")

    mock_request = MagicMock()
    mock_request.headers = {"X-Request-ID": "test-request-id"}
    mock_request.url.path = "/test-path"
    mock_request.method = "GET"

    response = await middleware.dispatch(mock_request, mock_call_next)

    assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
    response_body = json.loads(response.body.decode("utf-8"))
    assert response_body == {
        "detail": [
            {
                "msg": "An unexpected error occurred",
                "type": "server_error",
                "code": "GEN_999",
                "request_id": "test-request-id",
                "timestamp": response_body["detail"][0]["timestamp"],
                "environment": settings.ENVIRONMENT,
            }
        ]
    }
