"""
Test Helper Functions and Utilities
"""

from typing import Dict, Any


def validate_user_response_schema(user_data: Dict[str, Any]) -> None:
    """Validate that user response data conforms to expected schema."""
    required_fields = ["user_id", "user_email", "user_first_name", "user_country_code", "is_email_verified"]
    for field in required_fields:
        assert field in user_data, f"Missing required field: {field}"
    
    assert isinstance(user_data["user_id"], str)
    assert isinstance(user_data["user_email"], str)
    assert isinstance(user_data["user_first_name"], str) 
    assert isinstance(user_data["user_country_code"], str)
    assert isinstance(user_data["is_email_verified"], bool)


def validate_token_response_schema(token_data: Dict[str, Any]) -> None:
    """Validate that token response data conforms to expected schema."""
    required_fields = ["access_token", "refresh_token", "token_type"]
    for field in required_fields:
        assert field in token_data, f"Missing required field: {field}"
        
    assert isinstance(token_data["access_token"], str)
    assert isinstance(token_data["refresh_token"], str)
    assert token_data["token_type"] == "bearer"


def assert_http_error_response(response, expected_status: int, expected_message_contains: str = None):
    """Assert that an HTTP response is an error with expected format."""
    assert response.status_code == expected_status
    
    if expected_message_contains:
        response_data = response.json()
        if "detail" in response_data and isinstance(response_data["detail"], list):
            error_msg = response_data["detail"][0]["msg"]
            assert expected_message_contains.lower() in error_msg.lower()
        else:
            assert expected_message_contains.lower() in str(response_data).lower()


def create_mock_user_unit_of_work(mocker, methods_to_mock: Dict[str, Any] = None):
    """
    Create a mocked UserUnitOfWork with async context manager support.
    
    Args:
        mocker: pytest-mock mocker
        methods_to_mock: Dict of method names to return values
    """
    mock_uow = mocker.AsyncMock()
    
    if methods_to_mock:
        for method_name, return_value in methods_to_mock.items():
            if callable(return_value):
                setattr(mock_uow, method_name, mocker.AsyncMock(side_effect=return_value))
            else:
                setattr(mock_uow, method_name, mocker.AsyncMock(return_value=return_value))
    
    # Mock the context manager
    mock_uow_class = mocker.patch("app.api.v1.registration.UserUnitOfWork")
    mock_uow_class.return_value.__aenter__ = mocker.AsyncMock(return_value=mock_uow)
    mock_uow_class.return_value.__aexit__ = mocker.AsyncMock(return_value=None)
    
    return mock_uow


def create_test_user_data(email_suffix: str = "", **overrides) -> Dict[str, Any]:
    """
    Create standardized test user data.
    
    Args:
        email_suffix: Suffix to add to email for uniqueness
        **overrides: Fields to override in the default data
    """
    base_data = {
        "user_email": f"test{email_suffix}@example.com",
        "user_password": "TestPass123!@",
        "user_first_name": "Test",
        "user_country_code": "GB",
    }
    base_data.update(overrides)
    return base_data
