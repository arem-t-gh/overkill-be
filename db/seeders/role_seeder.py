from sqlalchemy.ext.asyncio import AsyncSession

from role.constants import ADMIN_ROLE_ID, ADMIN_ROLE_NAME, USER_ROLE_ID, USER_ROLE_NAME
from role.models import Role


async def seed_roles(db_session: AsyncSession):
    """Seed roles."""

    # TODO: Log start
    admin_role = Role(id=ADMIN_ROLE_ID, name=ADMIN_ROLE_NAME)

    user_role = Role(id=USER_ROLE_ID, name=USER_ROLE_NAME)

    # TODO: find out an upsert that would work for all db
    db_session.add(admin_role)
    db_session.add(user_role)
    await db_session.commit()

    # TODO: Log finish
