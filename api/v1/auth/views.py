from typing import Annotated

from fastapi import APIRouter, Depends
from supabase_auth.types import AuthResponse

from api.v1.auth.schemas import SignInRequest, SignUpRequest
from auth.service import (
    get_current_user,
    sign_up as auth_sign_up,
)
from db.database import DBSession
from supabase_app.auth.service import sign_in as sb_sign_in
from user.models import UserRead

router = APIRouter()


# @router.post("/sign-in")
# async def sign_in(request: SignInRequest) -> AuthResponse:
#     """Supabase sign in."""
#     result = sb_sign_in(request.email, request.password)
#     return result


# EXPERIMENTAL. REMOVE THIS AND DO SOMETHING BETTER.
@router.post("/access-token")
async def access_token(request: SignInRequest) -> AuthResponse:
    """Supabase sign in."""
    # EXPERIMENTAL. REMOVE THIS AND DO SOMETHING BETTER.
    result = sb_sign_in(request.email, request.password)

    return result


@router.get("/current-user")
async def current_user(
    user: Annotated[UserRead, Depends(get_current_user)],
) -> UserRead:
    """Get current user"""
    return user


@router.post("/sign-up")
async def sign_up(db_session: DBSession, request: SignUpRequest) -> UserRead:
    """Supabase sign up."""
    new_user = await auth_sign_up(db_session, request.email, request.password)
    return new_user
