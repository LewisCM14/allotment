"""
User Active Varieties Unit of Work
- Coordinates activation state for user grow guides.
- Ensures transactional integrity when adding or removing active varieties.
"""

from __future__ import annotations

import uuid
from types import TracebackType
from typing import List, Optional, Type

import structlog
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.factories.user_active_variety_factory import UserActiveVarietyFactory
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.exception_handler import (
    BusinessLogicError,
    ResourceNotFoundError,
)
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)
from app.api.models.user.user_model import UserActiveVariety
from app.api.repositories.grow_guide.variety_repository import VarietyRepository
from app.api.repositories.user.user_repository import UserRepository

logger = structlog.get_logger()


class UserActiveVarietiesUnitOfWork:
    """Unit of Work for managing user active varieties."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.user_repo = UserRepository(db)
        self.variety_repo = VarietyRepository(db)
        self.request_id = request_id_ctx_var.get()

    async def __aenter__(self) -> "UserActiveVarietiesUnitOfWork":
        logger.debug(
            "Starting user active varieties unit of work",
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
            logger.debug("Transaction rolled back", **log_context)
        else:
            try:
                with log_timing("user_active_varieties_commit", **log_context):
                    await self.db.commit()
                    logger.debug(
                        "Transaction committed successfully",
                        transaction="commit",
                        **log_context,
                    )
            except IntegrityError as exc:  # pragma: no cover - defensive guard
                await self.db.rollback()
                sanitized_error = sanitize_error_message(str(exc))
                logger.error(
                    "Integrity error committing user active varieties",
                    error=sanitized_error,
                    error_type="IntegrityError",
                    **log_context,
                )
                raise

    @translate_db_exceptions
    async def get_active_varieties(self, user_id: str) -> List[UserActiveVariety]:
        """Return all active varieties for the specified user."""
        parsed_user_id = self._parse_uuid(user_id, "user_id")
        with log_timing(
            "uow_get_active_varieties",
            request_id=self.request_id,
            user_id=user_id,
        ):
            return await self.user_repo.get_active_varieties(str(parsed_user_id))

    @translate_db_exceptions
    async def activate_variety(
        self, user_id: str, variety_id: str
    ) -> UserActiveVariety:
        """Mark a variety as active for the given user."""
        parsed_user_id = self._parse_uuid(user_id, "user_id")
        parsed_variety_id = self._parse_uuid(variety_id, "variety_id")

        log_context = {
            "user_id": user_id,
            "variety_id": variety_id,
            "request_id": self.request_id,
        }

        with log_timing("uow_activate_variety", **log_context):
            variety = await self.variety_repo.get_variety_owned_by_user(
                parsed_variety_id, parsed_user_id
            )
            if variety is None:
                logger.warning(
                    "Variety not found for activation",
                    **log_context,
                )
                raise ResourceNotFoundError("Variety", variety_id)

            existing = await self.user_repo.get_active_variety(
                parsed_user_id, parsed_variety_id
            )
            if existing:
                logger.info(
                    "Variety already active for user",
                    **log_context,
                )
                return existing

            association = UserActiveVarietyFactory.create(
                parsed_user_id, parsed_variety_id
            )
            created = await self.user_repo.add_active_variety(association)
            logger.info(
                "User active variety created",
                **log_context,
            )
            return created

    @translate_db_exceptions
    async def deactivate_variety(self, user_id: str, variety_id: str) -> None:
        """Remove an active variety association for the given user."""
        parsed_user_id = self._parse_uuid(user_id, "user_id")
        parsed_variety_id = self._parse_uuid(variety_id, "variety_id")
        log_context = {
            "user_id": user_id,
            "variety_id": variety_id,
            "request_id": self.request_id,
        }

        with log_timing("uow_deactivate_variety", **log_context):
            deleted = await self.user_repo.delete_active_variety(
                parsed_user_id, parsed_variety_id
            )
            if not deleted:
                logger.warning(
                    "Attempted to deactivate non-existent active variety",
                    **log_context,
                )
                raise ResourceNotFoundError("Active variety", variety_id)
            logger.info(
                "User active variety removed",
                **log_context,
            )

    def _parse_uuid(self, value: str, field: str) -> uuid.UUID:
        try:
            return uuid.UUID(str(value))
        except (TypeError, ValueError) as exc:
            logger.debug(
                "Invalid UUID format received",
                field=field,
                value=value,
                request_id=self.request_id,
            )
            raise BusinessLogicError(
                message=f"Invalid {field} format: {value}",
                status_code=400,
            ) from exc
