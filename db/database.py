from typing import Annotated, AsyncGenerator

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import DB_URI


class Base(DeclarativeBase):
    pass


# Acts as the connection layer
engine = create_async_engine(
    DB_URI,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,
    pool_recycle=1800,
    pool_timeout=20,
)


# Acts as the write layer
AsyncSessionLocal: async_sessionmaker[AsyncSession] = async_sessionmaker(
    bind=engine,
    autoflush=False,
    expire_on_commit=False,  # After commit, don’t expire objects. Keep their data around.
)

# Q: No autocommit=False?
# A: Removed in SQLAlchemy 2.0.
# https://docs.sqlalchemy.org/en/21/changelog/migration_20.html#autocommit-mode-removed-from-session-autobegin-support-added


async def get_db_session() -> AsyncGenerator[AsyncSession, None]:
    """DB session dependency injector."""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            # Discard the current transaction in progress.
            # https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block
            await session.rollback()
            raise

    # Q: Why not use the `with session.begin()` pattern to handle the rollback automatically?
    # A: That pattern implicitly does commit on success and rollback on error
    # A: The automatic rollback is fine. But we want to handle the commit inside the business layer manually.
    # https://docs.sqlalchemy.org/en/20/orm/session_basics.html#framing-out-a-begin-commit-rollback-block


DBSession = Annotated[AsyncSession, Depends(get_db_session)]
