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
from app.api.middleware.logging_middleware import (
    request_id_ctx_var,
    sanitize_error_message,
)

settings.SLOW_QUERY_THRESHOLD = getattr(settings, "SLOW_QUERY_THRESHOLD", 1.0)

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
    pool_pre_ping=True,
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
            sanitized_error = sanitize_error_message(str(e))
            logger.error(
                "Database session error",
                session_id=session_id,
                error=sanitized_error,
                exc_info=True,
            )
            await db.rollback()
            logger.info("Database session rolled back", session_id=session_id)
            raise
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
        session_id=id(conn),
        statement=statement[:200] + "..." if len(statement) > 200 else statement,
        parameters=sanitize_error_message(str(parameters)),
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
        session_id=id(conn),
        execution_time=f"{total:.3f}s",
        statement=statement[:200] + "..." if len(statement) > 200 else statement,
        request_id=request_id_ctx_var.get(),
    )

    # Log slow queries as warnings
    if total > settings.SLOW_QUERY_THRESHOLD:
        logger.warning(
            "Slow query detected",
            session_id=id(conn),
            execution_time=f"{total:.3f}s",
            statement=statement,
            parameters=sanitize_error_message(str(parameters)),
            request_id=request_id_ctx_var.get(),
        )


logger.info("Database module initialized successfully")
