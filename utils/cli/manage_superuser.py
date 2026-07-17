# import typer

import logging
from contextlib import asynccontextmanager

from cyclopts import App

from db import alembic_models  # noqa
from db.database import get_db_session
from role.constants import SUPERUSER_ROLE_ID
from user.models import User
from user.service import get_user_by_external_auth_id

logger = logging.getLogger(__name__)

app = App()

db_session_async_ctx = asynccontextmanager(get_db_session)


@app.command()
async def create_user_record(external_auth_id: str):
    """Create a super user record for an existing Supabase user.

    Parameters
    ----------
    external_auth_id
        Supabase Auth UID
    """
    async with db_session_async_ctx() as db_session:
        try:
            user = User(external_auth_id=external_auth_id, role_id=SUPERUSER_ROLE_ID)

            db_session.add(user)
            await db_session.commit()
            logger.info(
                "Created superuser record for external_auth_id=%s", external_auth_id
            )
        except Exception:
            logger.exception(
                "Failed to create superuser record for external_auth_id=%s",
                external_auth_id,
            )
            raise


@app.command()
async def delete_user_record(external_auth_id: str):
    """Delete a super user record.
    Parameters
    ----------
    external_auth_id
        Supabase Auth UID
    """
    async with db_session_async_ctx() as db_session:
        try:
            user = await get_user_by_external_auth_id(db_session, external_auth_id)
            await db_session.delete(user)
            await db_session.commit()
            logger.info(
                "Deleted superuser record for external_auth_id=%s", external_auth_id
            )
        except Exception:
            logger.exception(
                "Failed to delete superuser record for external_auth_id=%s",
                external_auth_id,
            )
            raise


if __name__ == "__main__":
    app()
