"""
User Unit of Work
- Manages user-related transactions as a single unit of work.
- Coordinates operations across the UserRepository and ensures atomicity.
- Handles transaction management (commit/rollback) for user-related operations.
"""

from types import TracebackType
from typing import TYPE_CHECKING, Any, Dict, Optional, Type

import structlog
from authlib.jose import jwt
from fastapi import HTTPException, status
from pydantic import ValidationError
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.auth_utils import (
    create_token,
)
from app.api.core.config import settings
from app.api.core.logging import log_timing
from app.api.factories.user_factory import UserFactory
from app.api.middleware.error_handler import (
    translate_db_exceptions,
    translate_token_exceptions,
)
from app.api.middleware.exception_handler import (
    DatabaseIntegrityError,
    InvalidTokenError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_allotment_schema import (
    UserAllotmentCreate,
    UserAllotmentUpdate,
)
from app.api.schemas.user.user_schema import UserCreate
from app.api.services.email_service import (
    send_password_reset_email,
    send_verification_email,
)

if TYPE_CHECKING:
    from app.api.models.user.user_model import UserAllotment

logger = structlog.get_logger()


class UserUnitOfWork:
    """Unit of Work for managing user-related transactions."""

    def __init__(self, db: AsyncSession):
        self.db = db
        self.user_repo = UserRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "UserUnitOfWork":
        """Enter the runtime context for the Unit of Work."""
        logger.debug(
            "Starting user unit of work",
            request_id=self.request_id,
            transaction="begin",
        )
        return self

    async def __aexit__(
        self,
        exc_type: Optional[Type[BaseException]],
        exc_value: Optional[BaseException],
        traceback: Optional[TracebackType],
    ) -> None:
        """Exit the runtime context for the Unit of Work."""
        log_context = {"request_id": self.request_id}

        if exc_type:
            if exc_value:
                sanitized_error = sanitize_error_message(str(exc_value))
                logger.warning(
                    "Rolling back transaction due to error",
                    error=sanitized_error,
                    error_type=exc_type.__name__,
                    **log_context,
                )
            else:
                logger.warning(
                    "Rolling back transaction due to unknown error",
                    error_type=str(exc_type),
                    **log_context,
                )
            await self.db.rollback()
            logger.debug(
                "Transaction rolled back", transaction="rollback", **log_context
            )
        else:
            try:
                with log_timing("db_commit"):
                    await self.db.commit()
                    logger.debug(
                        "Transaction committed successfully",
                        transaction="commit",
                        **log_context,
                    )
            except IntegrityError as ie:
                sanitized_error = sanitize_error_message(str(ie))
                logger.error(
                    "Database integrity error during commit",
                    error=sanitized_error,
                    error_type="IntegrityError",
                    exc_info=True,
                )
                raise DatabaseIntegrityError(message="User already has an allotment")

    @translate_db_exceptions
    async def create_user(self, user_data: UserCreate) -> User:
        """Create a new user."""
        safe_context = {
            "email": user_data.user_email,
            "request_id": self.request_id,
            "operation": "create_user_uow",
        }

        logger.info("Creating user via unit of work", **safe_context)

        with log_timing(
            "create_user_transaction", request_id=safe_context["request_id"]
        ):
            try:
                user = UserFactory.create_user(user_data)
                self.db.add(user)
            except ValidationError:
                raise
            except Exception as exc:
                logger.error("Error creating user", error=str(exc), **safe_context)
                raise

            safe_context["user_id"] = str(user.user_id)
            logger.info("User created in unit of work", **safe_context)

            return user

    @translate_db_exceptions
    async def verify_email(self, user_id: str) -> User:
        """Verify a user's email."""
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "verify_email_uow",
        }

        logger.debug("Verifying email via unit of work", **log_context)

        with log_timing(
            "verify_email_transaction", request_id=log_context["request_id"]
        ):
            user = await self.user_repo.verify_email(user_id)

            if not user.is_email_verified:
                user.is_email_verified = True
                await self.db.commit()
                logger.info(
                    "Email verified in unit of work",
                    previous_status=False,
                    new_status=True,
                    **log_context,
                )

            return user

    @translate_db_exceptions
    async def request_password_reset(self, user_email: str) -> Dict[str, str]:
        """Process a password reset request.

        Args:
            user_email: The email address to send the reset link to

        Returns:
            Dict with status and message
        """
        log_context = {
            "email": user_email,
            "request_id": self.request_id,
            "operation": "request_password_reset_uow",
        }

        logger.debug("Processing password reset request via UOW", **log_context)
        user = await self.user_repo.get_user_by_email(user_email)

        if not user:
            logger.warning("User not found for password reset", **log_context)
            return {
                "status": "no_user",
                "message": "If your email exists in our system and is verified, you will receive a password reset link shortly.",
            }

        log_context["user_id"] = str(user.user_id)
        log_context["is_verified"] = str(user.is_email_verified)

        if not user.is_email_verified:
            logger.info(
                "Password reset requested for unverified email - sending verification email instead",
                **log_context,
            )
            timing_context = {k: v for k, v in log_context.items() if k != "operation"}
            with log_timing("send_verification_email", **timing_context):
                await send_verification_email(
                    user_email=user_email, user_id=str(user.user_id), from_reset=True
                )
                return {
                    "status": "unverified",
                    "message": "Your email is not verified. We've sent you a verification email instead.",
                }

        timing_context = {k: v for k, v in log_context.items() if k != "operation"}
        with log_timing("create_reset_token", **timing_context):
            token = create_token(
                user_id=str(user.user_id),
                token_type="reset",
            )
            reset_url = f"{settings.FRONTEND_URL}/set-new-password?token={token}"

            await send_password_reset_email(user_email=user_email, reset_url=reset_url)
            logger.info("Password reset email sent", **log_context)

            return {
                "status": "success",
                "message": "If your email exists in our system and is verified, you will receive a password reset link shortly.",
            }

    @translate_db_exceptions
    async def reset_password(self, token: str, new_password: str) -> User:
        """Reset a user's password with a token.

        Args:
            token: The reset token
            new_password: The new password

        Returns:
            The updated user

        Raises:
            InvalidTokenError: If the token is invalid
            ValidationError: If the password doesn't meet requirements
        """
        log_context = {
            "request_id": self.request_id,
            "operation": "reset_password_uow",
        }

        logger.debug("Processing password reset via UOW", **log_context)

        payload = await self._decode_token(token, log_context)
        if payload.get("type") != "reset":
            logger.warning(
                "Invalid token type for password reset",
                expected="reset",
                received=payload.get("type"),
                **log_context,
            )
            raise InvalidTokenError("Invalid token type: expected reset token")

        user_id = payload.get("sub")
        if not user_id:
            logger.warning("Missing subject in reset token", **log_context)
            raise InvalidTokenError("Invalid token - no user ID found")

        log_context["user_id"] = user_id

        UserFactory.validate_password(new_password)

        user = await self.user_repo.update_user_password(user_id, new_password)

        log_context["email"] = user.user_email
        logger.info("Password reset successful", **log_context)

        return user

    @translate_token_exceptions
    async def _decode_token(
        self, token: str, log_context: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Decode and validate a JWT token.

        Args:
            token: The JWT token to decode
            log_context: Logging context

        Returns:
            The decoded token payload

        Raises:
            InvalidTokenError: If token is invalid
        """
        decoded = jwt.decode(
            token,
            settings.PUBLIC_KEY,
            claims_options={"exp": {"essential": True}},
        )
        return dict(decoded)

    @translate_db_exceptions
    async def create_user_allotment(
        self, user_id: str, allotment_data: UserAllotmentCreate
    ) -> "UserAllotment":
        """Create a new allotment for a user."""
        log_context = {"user_id": str(user_id), "request_id": self.request_id}
        logger.info(
            "Creating user allotment via unit of work",
            operation="create_user_allotment_uow",
            **log_context,
        )
        with log_timing("uow_create_user_allotment", request_id=self.request_id):
            allotment = await self.user_repo.create_user_allotment(
                user_id, allotment_data
            )
            return allotment

    @translate_db_exceptions
    async def get_user_allotment(self, user_id: str) -> "UserAllotment":
        """Fetch a user's allotment by user_id."""
        log_context = {"user_id": str(user_id), "request_id": self.request_id}
        logger.info(
            "Fetching user allotment via unit of work",
            operation="uow_get_user_allotment",
            **log_context,
        )
        with log_timing("uow_get_user_allotment", request_id=self.request_id):
            allotment = await self.user_repo.get_user_allotment(user_id)
            if not allotment:
                logger.warning("No allotment found", **log_context)
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Allotment not found",
                )
            return allotment

    @translate_db_exceptions
    async def update_user_allotment(
        self, user_id: str, allotment_data: UserAllotmentUpdate
    ) -> "UserAllotment":
        """Update a user's allotment."""
        log_context = {"user_id": str(user_id), "request_id": self.request_id}
        logger.info(
            "Updating user allotment via unit of work",
            operation="uow_update_user_allotment",
            **log_context,
        )
        with log_timing("uow_update_user_allotment", request_id=self.request_id):
            allotment = await self.user_repo.update_user_allotment(
                user_id, allotment_data
            )
            return allotment

    @translate_db_exceptions
    async def register_user(self, user_data: UserCreate) -> User:
        """Register a new user with email verification."""
        safe_context = {
            "email": user_data.user_email,
            "request_id": self.request_id,
            "operation": "register_user_uow",
        }

        logger.info("Registering user via unit of work", **safe_context)

        with log_timing(
            "register_user_transaction", request_id=safe_context["request_id"]
        ):
            try:
                user = UserFactory.create_user(user_data)
                created_user = await self.user_repo.create_user(user)

                # Send verification email
                await send_verification_email(
                    created_user.user_email, str(created_user.user_id)
                )

                safe_context["user_id"] = str(created_user.user_id)
                logger.info(
                    "User registered and verification email sent", **safe_context
                )

                return created_user
            except ValidationError:
                raise
            except Exception as exc:
                logger.error("Error registering user", error=str(exc), **safe_context)
                raise

    @translate_db_exceptions
    async def verify_user_email(self, user_id: str) -> User:
        """Verify a user's email by user ID."""
        return await self.verify_email(user_id)

    @translate_db_exceptions
    async def get_user_by_email(self, email: str) -> Optional[User]:
        """Get a user by email address."""
        log_context = {
            "email": email,
            "request_id": self.request_id,
            "operation": "get_user_by_email_uow",
        }

        logger.debug("Getting user by email via unit of work", **log_context)
        return await self.user_repo.get_user_by_email(email)

    @translate_db_exceptions
    async def update_user_profile(
        self, user_id: str, first_name: str, country_code: str
    ) -> User:
        """Update a user's profile information.

        Args:
            user_id: The user's ID
            first_name: The new first name
            country_code: The new country code

        Returns:
            The updated user

        Raises:
            UserNotFoundError: If the user is not found
            InvalidTokenError: If the user ID format is invalid
        """
        log_context: dict[str, Any] = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "update_user_profile_uow",
        }

        logger.info("Updating user profile", **log_context)

        with log_timing("uow_update_user_profile", request_id=self.request_id):
            user = await self.user_repo.update_user_profile(
                user_id, first_name, country_code
            )

            log_context["updated_fields"] = {
                "first_name": first_name,
                "country_code": country_code,
            }
            logger.info("User profile updated successfully", **log_context)
            return user

    @translate_db_exceptions
    async def get_user_feed_days(self, user_id: str) -> Any:
        """Get user's feed day preferences."""
        log_context = {
            "user_id": user_id,
            "request_id": self.request_id,
            "operation": "get_user_feed_days_uow",
        }

        logger.info("Getting user feed days", **log_context)

        with log_timing("uow_get_user_feed_days", request_id=self.request_id):
            user_feed_days = await self.user_repo.get_user_feed_days(user_id)
            return user_feed_days

    @translate_db_exceptions
    async def update_user_feed_day(
        self, user_id: str, feed_id: str, day_id: str
    ) -> Any:
        """Update a single user feed day preference."""
        log_context = {
            "user_id": user_id,
            "feed_id": feed_id,
            "day_id": day_id,
            "request_id": self.request_id,
            "operation": "update_user_feed_day_uow",
        }

        logger.info("Updating user feed day preference", **log_context)

        with log_timing("uow_update_user_feed_day", request_id=self.request_id):
            result = await self.user_repo.update_user_feed_day(user_id, feed_id, day_id)
            return result
