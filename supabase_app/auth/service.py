from supabase_app import sb
from supabase_auth.types import AuthResponse, UserResponse


def email_sign_up(email: str, password: str) -> AuthResponse:
    """Supabase email sign up."""
    response = sb.auth.sign_up({"email": email, "password": password})

    return response


def email_sign_in(email: str, password: str) -> AuthResponse:
    """Supabase email sign in."""
    response = sb.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    return response


def get_user_via_access_token(token: str) -> UserResponse | None:
    """Fetch the user object from supabase via access token."""
    response = sb.auth.get_user(token)

    return response
