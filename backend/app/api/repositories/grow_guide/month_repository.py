"""
Month Repository
- Encapsulates the logic required to access the Month table.
"""

from typing import List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.models.grow_guide.calendar_model import Month

logger = structlog.get_logger()


class MonthRepository:
    """Month repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.request_id = request_id_ctx_var.get()

    @translate_db_exceptions
    async def get_all_months(self) -> List[Month]:
        """Get all months of the year."""
        with log_timing("db_get_all_months", request_id=self.request_id):
            result = await self.db.execute(select(Month).order_by(Month.month_number))
            return list(result.scalars().all())
