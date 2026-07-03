from pydantic import EmailStr
from supabase_auth.errors import AuthApiError
from supabase_auth.types import AuthResponse, UserResponse

from supabase_app import SBClient


async def sign_up(sb_client: SBClient, email: EmailStr, password: str) -> AuthResponse:
    """Supabase email sign up."""
    response = await sb_client.auth.sign_up({"email": email, "password": password})

    return response


async def sign_in(sb_client: SBClient, email: EmailStr, password: str) -> AuthResponse:
    """Supabase email sign in."""
    response = await sb_client.auth.sign_in_with_password(
        {
            "email": email,
            "password": password,
        }
    )

    return response


async def get_user_by_access_token(
    sb_client: SBClient, token: str
) -> UserResponse | None:
    """Fetch the user object from supabase by access token."""
    response = await sb_client.auth.get_user(token)

    return response


async def delete_user(sb_client: SBClient, uid: str) -> bool:
    """Delete supabase auth user."""
    try:
        await sb_client.auth.admin.delete_user(uid)
        return True
    except AuthApiError as e:
        if e.code == "user_not_found":
            return False
        raise e
