from fastapi import HTTPException, status
from sqlalchemy import select

from db.database import DBSession
from role.constants import USER_ROLE_ID
from supabase_app import SBClient
from supabase_app.auth.service import delete_user as sb_delete_user
from user.models import NewUserRead, User, UserRead, UserUpdate


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
) -> User | None:
    """Get user by external auth id"""
    statement = select(User).where(User.external_auth_id == external_auth_id)
    result = await db_session.execute(statement)
    return result.scalar_one_or_none()


async def get_user_by_id(db_session: DBSession, id: int) -> User | None:
    """Get user by id"""
    statement = select(User).where(User.id == id)
    result = await db_session.execute(statement)
    return result.scalar_one_or_none()


async def update_user(db_session: DBSession, id: int, details: UserUpdate) -> UserRead:
    """Update user."""
    user = await get_user_by_id(db_session, id)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User is not found.",
        )

    user.name = details.name
    await db_session.commit()

    return UserRead.model_validate(user)


async def delete_user_via_external_auth_id(
    db_session: DBSession, sb_client: SBClient, external_auth_id: str
) -> bool:
    """Delete user."""

    # Delete in supabase
    sb_auth_delete_status = await sb_delete_user(sb_client, external_auth_id)

    user_in_db = await get_user_by_external_auth_id(db_session, external_auth_id)
    user_in_db_delete_status = False

    if user_in_db:
        # Delete in db
        await db_session.delete(user_in_db)
        await db_session.commit()

        user_in_db_delete_status = True

    return sb_auth_delete_status or user_in_db_delete_status
