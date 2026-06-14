from fastapi import APIRouter

from supabase_app.auth.service import (
    email_sign_up as sb_email_sign_up,
    email_sign_in as sb_email_sign_in,
)
from supabase_auth.types import AuthResponse

# , UserResponse
from api.v1.schemas.supabase.auth_schemas import EmailSignIn, EmailSignUp

router = APIRouter()


@router.post("/email-sign-up")
def email_sign_up(request: EmailSignUp) -> AuthResponse:
    """Supabase email sign in."""
    response = sb_email_sign_up(request.email, request.password)

    return response


@router.post("/email-sign-in")
def email_sign_in(request: EmailSignIn) -> AuthResponse:
    """Supabase email sign in."""
    response = sb_email_sign_in(request.email, request.password)

    return response


# Use get current user dependency here
# @router.get("/current-user")
# def current_user(access_token: str) -> UserResponse | None:
