"""
Database Connection
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import declarative_base, sessionmaker

from app.api.core.config import settings

engine = create_async_engine(
    settings.DATABASE_URL, pool_size=10, max_overflow=5, echo=False
)

AsyncSessionLocal = sessionmaker(
    bind=engine, class_=AsyncSession, expire_on_commit=False
)


Base = declarative_base()


async def get_db():
    """Dependency to get async database session"""
    async with AsyncSessionLocal() as session:
        yield session
