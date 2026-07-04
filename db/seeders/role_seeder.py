from sqlalchemy.ext.asyncio import AsyncSession

from role.constants import (
    ADMIN_ROLE_ID,
    ADMIN_ROLE_NAME,
    SUPERUSER_ROLE_ID,
    SUPERUSER_ROLE_NAME,
    USER_ROLE_ID,
    USER_ROLE_NAME,
)
from role.models import Role


async def seed_roles(db_session: AsyncSession):
    """Seed roles in an idempotent manner."""

    # TODO: Log start
    roles = [
        Role(id=SUPERUSER_ROLE_ID, name=SUPERUSER_ROLE_NAME),
        Role(id=ADMIN_ROLE_ID, name=ADMIN_ROLE_NAME),
        Role(id=USER_ROLE_ID, name=USER_ROLE_NAME),
    ]

    for role in roles:
        await db_session.merge(role)
    await db_session.commit()

    # TODO: Log finish
