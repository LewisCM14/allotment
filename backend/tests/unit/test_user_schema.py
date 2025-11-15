import pytest

from app.api.schemas.user.user_schema import (
    EmailRequest,
    PasswordResetRequest,
    UserCreate,
    UserLogin,
)


def test_user_login_email_normalized_lowercase():
    user = UserLogin(user_email="TeSt@ExAmPlE.CoM", user_password="Password1!")
    assert user.user_email == "test@example.com"


def test_user_create_email_normalized_lowercase():
    user = UserCreate(
        user_email="TeSt@ExAmPlE.CoM",
        user_password="Password1!",
        user_first_name="John",
        user_country_code="GB",
    )
    assert user.user_email == "test@example.com"


def test_email_request_normalized_lowercase():
    req = EmailRequest(user_email="TeSt@ExAmPlE.CoM")
    assert req.user_email == "test@example.com"


def test_password_reset_request_normalized_lowercase():
    req = PasswordResetRequest(user_email="TeSt@ExAmPlE.CoM")
    assert req.user_email == "test@example.com"
