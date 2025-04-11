"""
User Unit of Work
- Manages user-related transactions as a single unit of work.
- Coordinates operations across the UserRepository and ensures atomicity.
- Handles transaction management (commit/rollback) for user-related operations.
"""

from types import TracebackType
from typing import Optional, Type

import structlog
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.factories.user_factory import UserFactory
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models import User
from app.api.repositories.user.user_repository import UserRepository
from app.api.schemas.user.user_schema import UserCreate

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
            with log_timing("db_commit", **log_context):
                await self.db.commit()
                logger.debug(
                    "Transaction committed successfully",
                    transaction="commit",
                    **log_context,
                )

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
            user = UserFactory.create_user(user_data)
            self.db.add(user)

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

            log_context["email"] = user.user_email
            logger.info(
                "Email verified in unit of work",
                previous_status=False,
                new_status=True,
                **log_context,
            )

            return user
