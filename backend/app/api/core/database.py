"""
Database Connection
- Configures async SQLAlchemy session
- Provides database dependency for FastAPI
"""

import logging
import time
from typing import AsyncGenerator

import structlog
from sqlalchemy import event
from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import declarative_base

from app.api.core.config import settings

logger = structlog.get_logger()
logging.getLogger("sqlalchemy.engine").setLevel(logging.INFO)

engine: AsyncEngine = create_async_engine(
    settings.DATABASE_URL,
    pool_size=10,
    max_overflow=5,
    echo=False,
)

AsyncSessionLocal = async_sessionmaker[AsyncSession](
    bind=engine,
    expire_on_commit=False,
    autoflush=False,
    class_=AsyncSession,
)

Base = declarative_base()


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """Get async database session.

    Yields:
        AsyncSession: SQLAlchemy async session
    """
    async with AsyncSessionLocal() as db:
        try:
            yield db
        except Exception as e:
            logger.error("Database error", error=str(e), exc_info=True)
            await db.rollback()
        finally:
            await db.close()


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    conn.info.setdefault("query_start_time", []).append(time.monotonic())


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(conn, cursor, statement, parameters, context, executemany):
    total = time.monotonic() - conn.info["query_start_time"].pop(-1)
    if total > 1.0:  # Log only slow queries (>1s)
        print(f"Slow Query: {statement} took {total:.2f}s")
