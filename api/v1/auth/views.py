from typing import Annotated

from fastapi import APIRouter, Depends

from api.v1.auth.schemas import SignInRequest, SignUpRequest
from auth.models import UserReadWithAccessToken
from auth.service import (
    AuthorizedCurrentUser,
    get_current_user,
    sign_in as sign_in_service,
    sign_up as auth_sign_up,
)
from db.database import DBSession
from role.constants import ADMIN_ROLE_ID
from supabase_app import SBClient
from user.models import UserRead

router = APIRouter()


@router.post("/experimental-sign-in")
async def access_token(
    db_session: DBSession, sb_client: SBClient, request: SignInRequest
) -> UserReadWithAccessToken:
    """Supabase sign in."""
    # EXPERIMENTAL. REMOVE THIS AND DO SOMETHING BETTER.
    result = await sign_in_service(
        db_session, sb_client, request.email, request.password
    )

    return result


@router.post("/test-auth-check")
async def auth_check(
    user: Annotated[UserRead, Depends(AuthorizedCurrentUser([ADMIN_ROLE_ID]))],
) -> UserRead:
    """Test auth check"""
    return user


@router.get("/current-user")
async def current_user(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """Get current user"""
    return user


@router.post("/sign-up")
async def sign_up(
    db_session: DBSession, sb_client: SBClient, request: SignUpRequest
) -> UserRead:
    """Supabase sign up."""
    new_user = await auth_sign_up(
        db_session, sb_client, request.email, request.password
    )
    return new_user
