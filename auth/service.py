from typing import Annotated, List

from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials
from pydantic import EmailStr

from auth.models import UserReadWithAccessToken
from auth.security import http_bearer_scheme
from db.database import DBSession
from role.constants import USER_ROLE_ID
from supabase_app import SBClient
from supabase_app.auth.service import (
    get_user_by_access_token,
    sign_in as sb_sign_in,
    sign_up as sb_sign_up,
)
from user.models import UserRead
from user.service import create_user, get_user_by_external_auth_id


async def get_current_user(
    db_session: DBSession,
    sb_client: SBClient,
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_scheme)],
) -> UserRead | None:
    """Get current user from bearer (access) token."""

    response = await get_user_by_access_token(sb_client, credentials.credentials)

    if response:
        supabase_user = response.user
        user = await get_user_by_external_auth_id(db_session, supabase_user.id)
        return UserRead.model_validate(user)

    return None


class AuthorizedCurrentUser:
    """Check user's request authorization dependency."""

    def __init__(self, authorized_role_ids: List[int]):
        """Initialize with a list of ids allowed to access the route."""
        self.authorized_role_ids = authorized_role_ids

    async def __call__(self, user: UserRead = Depends(get_current_user)) -> UserRead:
        """FastAPI executes this method when the dependency is evaluated."""
        if user.role_id not in self.authorized_role_ids:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="You do not have the required permissions to access this resource.",
            )

        return user


async def sign_up(
    db_session: DBSession, sb_client: SBClient, email: EmailStr, password: str
) -> UserRead:
    """Sign up with external auth provider."""
    response = await sb_sign_up(sb_client, email, password)

    sb_user = response.user

    if sb_user:
        new_user = await create_user(
            db_session,
            sb_user.id,  # supabase uid
            USER_ROLE_ID,
        )

        return UserRead(**new_user.model_dump(), email=sb_user.email)

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User detail is not returned from Supabase.",
        )


async def sign_in(
    db_session: DBSession, sb_client: SBClient, email: EmailStr, password: str
) -> UserReadWithAccessToken:
    """Sign up with external auth provider."""

    response = await sb_sign_in(sb_client, email, password)

    sb_user = response.user
    access_token = response.session.access_token if response.session else None

    # If user exists in supabase auth but no user entity yet in db, create one
    if sb_user and access_token:
        user_in_db = await get_user_by_external_auth_id(db_session, sb_user.id)

        if user_in_db:
            user_in_db = UserRead.model_validate(user_in_db)
            user_in_db.email = sb_user.email
        else:
            new_user = await create_user(
                db_session,
                sb_user.id,  # supabase uid
                USER_ROLE_ID,
            )

            user_in_db = UserRead(**new_user.model_dump(), email=sb_user.email)

        return UserReadWithAccessToken(
            **user_in_db.model_dump(), access_token=access_token
        )

    else:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="User detail is not returned from Supabase.",
        )
