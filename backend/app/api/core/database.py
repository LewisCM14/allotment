"""
Database Connection
- Configures async SQLAlchemy session
- Provides database dependency for FastAPI
"""

import logging
import time
from typing import Any, AsyncGenerator

import structlog
from sqlalchemy import Connection, event
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


logger.info(
    "Initializing database connection", pool_size=10, max_overflow=5, echo=False
)

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
    session_id = id(AsyncSessionLocal)
    logger.debug("Creating new database session", session_id=session_id)

    async with AsyncSessionLocal() as db:
        try:
            logger.debug("Database session started", session_id=session_id)
            yield db
        except Exception as e:
            logger.error(
                "Database session error",
                session_id=session_id,
                error=str(e),
                exc_info=True,
            )
            await db.rollback()
            logger.info("Database session rolled back", session_id=session_id)
        finally:
            await db.close()
            logger.debug("Database session closed", session_id=session_id)


@event.listens_for(engine.sync_engine, "before_cursor_execute")
def before_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool,
) -> None:
    conn.info.setdefault("query_start_time", []).append(time.monotonic())

    logger.debug(
        "Starting database query",
        statement=statement[:200] + "..." if len(statement) > 200 else statement,
        executemany=executemany,
    )


@event.listens_for(engine.sync_engine, "after_cursor_execute")
def after_cursor_execute(
    conn: Connection,
    cursor: Any,
    statement: str,
    parameters: Any,
    context: Any,
    executemany: bool,
) -> None:
    total = time.monotonic() - conn.info["query_start_time"].pop(-1)

    logger.debug(
        "Query completed",
        execution_time=f"{total:.3f}s",
        statement=statement[:200] + "..." if len(statement) > 200 else statement,
    )

    # Log slow queries as warnings
    if total > 1.0:
        logger.warning(
            "Slow query detected",
            execution_time=f"{total:.3f}s",
            statement=statement,
            parameters=str(parameters),
        )


logger.info("Database module initialized successfully")
