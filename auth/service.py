from typing import Annotated
from fastapi.security import HTTPAuthorizationCredentials
from auth.security import http_bearer_scheme
from fastapi import Depends
from supabase_app.auth.service import get_user_by_access_token


def get_current_user(
    credentials: Annotated[HTTPAuthorizationCredentials, Depends(http_bearer_scheme)],
):
    """Get current user from bearer (access) token."""

    # TODO: should return data from db, update return type

    supabase_user = get_user_by_access_token(credentials.credentials)
    # user = db.query(supabase_user.id_or_something)

    return supabase_user
