import logging
from contextlib import asynccontextmanager

from fastapi import FastAPI

# To register models in Python upon running and prevent missing references error
from db import alembic_models  # noqa
from db.database import check_db_connection, get_engine

logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Log app startup/shutdown and fail fast if the DB isn't reachable."""
    logger.info("Application startup")
    await check_db_connection()

    yield

    # This runs every time, `--reload` included: a code change kills the
    # worker process and starts a fresh one, and that kill is a graceful
    # SIGTERM that triggers this shutdown path. dispose() isn't needed for
    # the connections to go away -- the OS reclaims those sockets on exit
    # regardless -- it's here so they're closed cleanly (proper
    # wire-protocol termination) instead of an abrupt teardown.
    await get_engine().dispose()
    logger.info("Application shutdown")


app = FastAPI(title="Overkill", lifespan=lifespan)
