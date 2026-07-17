import logging
from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DB_URI

logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


# These are lazy loaded to be test friendly and prevent unintended import side-effects.
_engine = None
_session_factory = None


def get_engine():
    """Lazy load engine singleton."""
    global _engine

    if _engine is None:
        logger.info("Creating DB engine (pool_size=10, max_overflow=20)")
        # Acts as the connection layer
        _engine = create_async_engine(
            DB_URI,
            pool_size=10,
            max_overflow=20,
            pool_pre_ping=True,
            pool_recycle=1800,
            pool_timeout=20,
        )
    return _engine


def get_session_factory():
    """Lazy load async session.

    It is a factory because everytime the session is called, it is a different session.
    Unlike a singleton which is the same thing everytime it's called.
    """
    global _session_factory
    if _session_factory is None:
        logger.info("Creating DB session factory")
        # Acts as the write layer
        _session_factory = async_sessionmaker(  # async_sessionamker is a factory itself.
            # Q: No autocommit=False?
            # A: Removed in SQLAlchemy 2.0.
            # https://docs.sqlalchemy.org/en/21/changelog/migration_20.html#autocommit-mode-removed-from-session-autobegin-support-added
            bind=get_engine(),
            autoflush=False,
            expire_on_commit=False,  # After commit, don’t expire objects. Keep their data around.
        )
    return _session_factory


async def check_db_connection() -> None:
    """Verify the DB is reachable. Meant to be called once at app startup so
    a misconfigured/unreachable DB fails the boot (and the container
    restarts/the deploy is flagged) instead of surfacing as a 500 on a
    user's first request.
    """
    try:
        async with get_engine().connect() as connection:
            await connection.execute(text("SELECT 1"))
        logger.info("DB connection check succeeded")
    except Exception:
        logger.exception("DB connection check failed")
        raise


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """DB session dependency injector."""

    # Q: Why not use the `with session.begin()` pattern to handle the rollback automatically?
    # A: That pattern implicitly does commit on success and rollback on error
    # A: The automatic rollback is fine. But we want to handle the commit inside the business layer manually.
    # https://docs.sqlalchemy.org/en/20/orm/session_basics.html#opening-and-closing-a-session
    # https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block

    async with get_session_factory()() as session:
        try:
            yield session
        except Exception:
            # Discard the current transaction in progress.
            # https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
            await session.rollback()
            raise


DBSession = Annotated[AsyncSession, Depends(get_db_session)]
