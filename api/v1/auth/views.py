from fastapi import APIRouter

from supabase_app.auth.service import (
    sign_up as sb_sign_up,
    sign_in as sb_sign_in,
)
from supabase_auth.types import AuthResponse

# , UserResponse
from api.v1.auth.schemas import SignInRequest, SignUpRequest

router = APIRouter()


@router.post("/sign-up")
def sign_up(request: SignUpRequest) -> AuthResponse:
    """Supabase sign up."""
    response = sb_sign_up(request.email, request.password)

    return response


@router.post("/sign-in")
def sign_in(request: SignInRequest) -> AuthResponse:
    """Supabase sign in."""
    response = sb_sign_in(request.email, request.password)

    return response


# Use get current user dependency here
# @router.get("/current-user")
# def current_user(access_token: str) -> UserResponse | None:
