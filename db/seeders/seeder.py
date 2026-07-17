import asyncio
import logging
from contextlib import asynccontextmanager

# To register all models in python upon running
from db import alembic_models  # noqa
from db.database import get_db_session
from db.seeders.role_seeder import seed_roles

logger = logging.getLogger(__name__)


async def run_all_seeders() -> None:
    """Run all seeders."""

    logger.info("Running seeders")

    # Since get_db_session is an async generator, we have to wrap it in asynccontextmanager to seamlessly use it with `async with` and let it handle the session resource management
    AsyncSeederSessionLocal = asynccontextmanager(get_db_session)
    async with AsyncSeederSessionLocal() as session:
        try:
            await seed_roles(session)

            await session.commit()

            logger.info("Seeders finished")

        except Exception:
            logger.exception("Seeders failed")
            raise


if __name__ == "__main__":
    asyncio.run(run_all_seeders())
