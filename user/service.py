from sqlalchemy import select

from db.database import DBSession
from role.constants import USER_ROLE_ID
from user.models import NewUserRead, User, UserRead


async def create_user(
    db_session: DBSession, external_auth_id: str, role_id: int = USER_ROLE_ID
) -> NewUserRead:
    """Create user."""
    new_user = User(external_auth_id=external_auth_id, role_id=role_id)

    db_session.add(new_user)
    await db_session.commit()

    return NewUserRead.model_validate(new_user)


async def get_user_by_external_auth_id(
    db_session: DBSession, external_auth_id: str
) -> UserRead | None:
    """Get user by external auth id"""
    statement = select(User).where(User.external_auth_id == external_auth_id)
    result = await db_session.execute(statement)
    user = result.scalar_one_or_none()

    return UserRead.model_validate(user) if user else None
