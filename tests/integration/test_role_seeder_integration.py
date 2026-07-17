from sqlalchemy import select

from db.seeders.role_seeder import seed_roles
from role.constants import (
    ADMIN_ROLE_ID,
    ADMIN_ROLE_NAME,
    SUPERUSER_ROLE_ID,
    SUPERUSER_ROLE_NAME,
    USER_ROLE_ID,
    USER_ROLE_NAME,
)
from role.models import Role


class TestSeedRolesIntegration:
    async def test_seeds_the_three_fixed_roles(self, db_session):
        # db_session's schema setup already runs seed_roles once; this asserts
        # what actually landed in Postgres rather than trusting the seeder blindly.
        result = await db_session.execute(select(Role))
        roles = {role.id: role.name for role in result.scalars().all()}

        assert roles == {
            SUPERUSER_ROLE_ID: SUPERUSER_ROLE_NAME,
            ADMIN_ROLE_ID: ADMIN_ROLE_NAME,
            USER_ROLE_ID: USER_ROLE_NAME,
        }

    async def test_running_seed_roles_again_is_idempotent(self, db_session):
        await seed_roles(db_session)
        await seed_roles(db_session)

        result = await db_session.execute(select(Role))
        roles = result.scalars().all()

        assert len(roles) == 3
