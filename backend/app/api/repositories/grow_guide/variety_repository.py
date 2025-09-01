"""
Variety Repository
- Encapsulate the logic required to access the: Variety, Variety Water Day, Planting Conditions, Feed, Lifecycle and Frequency tables.
"""

from typing import List

import structlog
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.core.logging import log_timing
from app.api.middleware.error_handler import translate_db_exceptions
from app.api.middleware.logging_middleware import request_id_ctx_var
from app.api.models.grow_guide.guide_options_model import Feed

logger = structlog.get_logger()


class VarietyRepository:
    """Variety repository for database operations."""

    def __init__(self, db: AsyncSession) -> None:
        self.db = db
        self.request_id = request_id_ctx_var.get()

    @translate_db_exceptions
    async def get_all_feeds(self) -> List[Feed]:
        """Get all available feed types."""
        with log_timing("db_get_all_feeds", request_id=self.request_id):
            result = await self.db.execute(select(Feed).order_by(Feed.feed_name))
            return list(result.scalars().all())
