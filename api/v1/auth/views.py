from fastapi import APIRouter

from supabase_app.auth.service import (
    sign_up as sb_sign_up,
    sign_in as sb_sign_in,
)
from supabase_auth.types import AuthResponse

from api.v1.auth.schemas import SignInRequest, SignUpRequest
from typing import Annotated
from fastapi import Depends
from auth.service import get_current_user

router = APIRouter()


@router.post("/sign-in")
def sign_in(request: SignInRequest) -> AuthResponse:
    """Supabase sign in."""
    result = sb_sign_in(request.email, request.password)

    return result


@router.get("/current-user")
def current_user(user: Annotated[dict, Depends(get_current_user)]):
    """Get current user"""
    # TODO: should return user from db not supabase
    # TODO: return type
    return user


@router.post("/sign-up")
def sign_up(request: SignUpRequest) -> AuthResponse:
    """Supabase sign up."""
    response = sb_sign_up(request.email, request.password)

    return response
