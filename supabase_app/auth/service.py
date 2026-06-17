from pydantic import EmailStr
from supabase_auth.types import AuthResponse, UserResponse

from supabase_app import sb


def sign_up(email: EmailStr, password: str) -> AuthResponse:
    """Supabase email sign up."""
    response = sb.auth.sign_up({"email": email, "password": password})

    return response


def sign_in(email: EmailStr, password: str) -> AuthResponse:
    """Supabase email sign in."""
    response = sb.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    return response


def get_user_by_access_token(token: str) -> UserResponse | None:
    """Fetch the user object from supabase by access token."""
    response = sb.auth.get_user(token)

    return response
