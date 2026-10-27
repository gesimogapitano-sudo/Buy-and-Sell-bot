
"""
Database engine and async session management.
"""

import logging
from typing import AsyncGenerator, Optional

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)

from app.config import get_settings

logger = logging.getLogger(__name__)

_engine: Optional[AsyncEngine] = None
_session_factory: Optional[async_sessionmaker[AsyncSession]] = None


def get_engine() -> AsyncEngine:
    """Get or create the async database engine."""
    global _engine

    if _engine is None:
        settings = get_settings()

        _engine = create_async_engine(
            settings.database_url,
            connect_args={"ssl": "require"},
            echo=(settings.log_level == "DEBUG"),
            pool_pre_ping=True,
            pool_size=5,
            max_overflow=5,
            pool_recycle=3600,
        )

        logger.info("Database engine created.")

    return _engine


def get_session_factory() -> async_sessionmaker[AsyncSession]:
    """Get or create the async session factory."""
    global _session_factory

    if _session_factory is None:
        _session_factory = async_sessionmaker(
            get_engine(),
            class_=AsyncSession,
            expire_on_commit=False,
        )

    return _session_factory


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide an async database session."""
    async with get_session_factory()() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def close_engine() -> None:
    """Dispose of the async database engine."""
    global _engine, _session_factory

    if _engine is not None:
        await _engine.dispose()
        _engine = None
        _session_factory = None
        logger.info("Database engine disposed.")


def reset_engine() -> None:
    """Reset engine state for testing."""
    global _engine, _session_factory

    _engine = None
    _session_factory = None
