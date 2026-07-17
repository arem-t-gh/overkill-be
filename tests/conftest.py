import logging
from typing import AsyncGenerator

import asyncpg
import pytest
from sqlalchemy import URL, make_url
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from config import TEST_DB_URI
from db import alembic_models  # noqa
from db.database import Base
from db.seeders.role_seeder import seed_roles

logger = logging.getLogger(__name__)


async def _ensure_test_database_exists(url: URL) -> None:
    """Create the configured test database on the Postgres server if it's missing.

    `url.database` comes from our own TEST_DB_URI config, not user input, so
    interpolating it into DDL here is safe (asyncpg can't parameterize identifiers).
    """
    connection = await asyncpg.connect(
        user=url.username,
        password=url.password,
        host=url.host,
        port=url.port or 5432,
        database="postgres",
    )
    try:
        exists = await connection.fetchval(
            "SELECT 1 FROM pg_database WHERE datname = $1", url.database
        )
        if not exists:
            logger.debug("Test database %r missing, creating it", url.database)
            await connection.execute(f'CREATE DATABASE "{url.database}"')
    finally:
        await connection.close()


@pytest.fixture
async def db_session() -> AsyncGenerator[AsyncSession, None]:
    """Real, isolated Postgres session for integration/e2e tests.

    Skips (rather than fails) when TEST_DB_URI isn't configured, e.g. when
    running outside the dev container. Schema is created and role reference
    data is seeded fresh per test, then dropped afterwards. Everything (engine,
    connection, session) is created and torn down within this single test's
    event loop on purpose: asyncpg connections are bound to the loop that
    created them, and pytest-asyncio hands out a new loop per test function
    here (`asyncio_default_fixture_loop_scope = "function"`), so a
    session-scoped engine shared across tests would break.
    """
    if not TEST_DB_URI:
        pytest.skip("TEST_DB_URI is not configured; skipping DB-backed test.")

    url = make_url(TEST_DB_URI)
    await _ensure_test_database_exists(url)

    engine = create_async_engine(TEST_DB_URI)

    logger.debug("Creating schema on test database %r", url.database)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    seed_session_factory = async_sessionmaker(
        bind=engine, autoflush=False, expire_on_commit=False
    )
    async with seed_session_factory() as seed_session:
        await seed_roles(seed_session)

    connection = await engine.connect()
    trans = await connection.begin()

    # --- DB session: fixture-owned transaction + SAVEPOINT-backed Sessions ---
    # SQLAlchemy recommends the use of join_transaction_mode and create_savepoint for test suites where DB is typically rolled back
    # From the docs "When the test tears down, the external transaction is rolled back so that any data changes throughout the test are reverted"
    # See https://docs.sqlalchemy.org/en/20/orm/session_transaction.html#joining-a-session-into-an-external-transaction-such-as-for-test-suites

    # So all transactions within the session when rollback() is called in the fixture, everything will be reverted, including those with commit()
    # This makes perfect test control. We want to make sure of clean ups between tests.
    # Unlike normal SQLAlchemy sessions, they end their transaction at every commit(). Here,
    # join_transaction_mode="create_savepoint" keeps the *same* outer `trans`
    # alive across every commit() in the test, so the fixture can roll it all
    # back in one shot at teardown.
    # In the test, we want to make sure it's using the same transaction throughout so we can clean it up easily.

    # Additionally, expanding on "create_savepoint" and its real value
    # Docs: "the external transaction will remain unaffected throughout the lifespan of the Session."
    # So, if ever, in the future, there would be rollback() in the middle of service logic (which would only rollback that granular scope),
    # Then that would keep the external transaction unaffected and still enforce that fixture scope rollback()

    # Setup/teardown note: only the test's own work runs inside `trans`.
    # Schema creation and role seeding happen earlier, in their own already-
    # committed transactions, before `trans` is opened.

    # --- autoflush=False (mirrors db/database.py's get_session_factory()) ---
    #
    # add(user); query(user)
    #   autoflush=True  -> query() auto-flushes the pending add() and finds the user
    #   autoflush=False -> query() runs as-is, pending add() not sent (not flushed) does not find (return) the user
    #
    # Either way, flush (not commit) is what actually sends SQL to Postgres;
    # commit is a separate, later step that also happens to flush first
    # and commit is what makes the data persist in the database across sessions in normal operations
    # But in this case, with the joint transaction, we are reverting even those commits.
    txn_session_factory = async_sessionmaker(
        bind=connection,
        autoflush=False,
        expire_on_commit=False,
        join_transaction_mode="create_savepoint",
    )
    session = txn_session_factory()

    yield session

    await session.close()
    await trans.rollback()
    await connection.close()

    logger.debug("Dropping schema on test database %r", url.database)
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
