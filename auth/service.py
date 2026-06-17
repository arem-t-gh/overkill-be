from typing import Annotated

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import EmailStr

from auth.security import http_bearer_scheme
from db.database import DBSession
from supabase_app.auth.service import (
    get_user_by_access_token,
    # sign_in as sb_sign_in,
    sign_up as sb_sign_up,
)
from user.models import UserRead
from user.service import create_user


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_scheme)],
) -> UserRead | None:
    """Get current user from bearer (access) token."""

    supabase_user = get_user_by_access_token(credentials.credentials)

    if supabase_user:
        user = supabase_user.user
        return UserRead(id=user.id, email=user.email)  # type: ignore

    return None


async def sign_up(db_session: DBSession, email: EmailStr, password: str) -> UserRead:
    """Sign up with external auth provider."""
    response = sb_sign_up(email, password)

    if response.user:
        new_user = response.user
        new_user = await create_user(db_session, new_user.id)

        return UserRead(id=new_user.id, email=email)

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User detail is not returned from Supabase.",
        )
