from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from fastapi.security import HTTPAuthorizationCredentials
from supabase_auth.types import AuthResponse, User, UserResponse

from auth.service import AuthorizedCurrentUser, get_current_user, sign_up
from role.constants import ADMIN_ROLE_ID, USER_ROLE_ID
from user.models import NewUserRead, UserRead


@patch("auth.service.get_user_by_access_token")
@patch("auth.service.get_user_by_external_auth_id", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_get_current_user_success(
    mock_get_user_by_external_auth_id,
    mock_get_user_by_access_token,
):
    """Test get current user on success."""
    db_session = MagicMock()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="access-token",
    )

    mock_user = UserRead(id=1, role_id=2, email="test@example.com")

    mock_user_response = UserResponse(
        user=User(
            id="11111111-1111-1111-1111-111111111111",
            app_metadata={
                "provider": "email",
                "providers": ["email"],
            },
            user_metadata={},
            aud="authenticated",
            created_at=datetime.fromisoformat("2024-06-17T00:19:25.760110+00:00"),
        )
    )

    mock_get_user_by_access_token.return_value = mock_user_response
    mock_get_user_by_external_auth_id.return_value = mock_user

    result = await get_current_user(db_session, credentials)

    mock_get_user_by_access_token.assert_called_once_with("access-token")
    mock_get_user_by_external_auth_id.assert_awaited_once_with(
        db_session, mock_user_response.user.id
    )

    assert result is mock_user


@patch("auth.service.get_user_by_access_token")
@pytest.mark.asyncio
async def test_get_current_user_returns_none_when_token_invalid(
    mock_get_user_by_access_token,
):
    """Test get current user returns none when token is invalid."""
    db_session = MagicMock()

    credentials = HTTPAuthorizationCredentials(
        scheme="Bearer",
        credentials="invalid-token",
    )

    mock_get_user_by_access_token.return_value = None

    result = await get_current_user(db_session, credentials)

    assert result is None
    mock_get_user_by_access_token.assert_called_once_with("invalid-token")


@pytest.mark.asyncio
async def test_authorized_current_user_allows_authorized_role():
    """Test an authorized user on authorization dependency."""
    dependency = AuthorizedCurrentUser([ADMIN_ROLE_ID])

    user = UserRead(
        id=1,
        role_id=ADMIN_ROLE_ID,
        email="test@example.com",
    )

    result = await dependency(user)

    assert result is user


@pytest.mark.asyncio
async def test_authorized_current_user_raises_forbidden():
    """Test a 403 on authorization dependency."""
    dependency = AuthorizedCurrentUser([ADMIN_ROLE_ID])

    user = UserRead(
        id=1,
        role_id=USER_ROLE_ID,
        email="test@example.com",
    )

    with pytest.raises(HTTPException) as exc:
        await dependency(user)

    assert exc.value.status_code == 403
    assert exc.value.detail == (
        "You do not have the required permissions to access this resource."
    )


@patch("auth.service.sb_sign_up")
@patch("auth.service.create_user", new_callable=AsyncMock)
@pytest.mark.asyncio
async def test_sign_up_success(
    mock_create_user,
    mock_sb_sign_up,
):
    """Test sign up success."""
    db_session = MagicMock()

    email = "test@example.com"
    password = "password123"

    mock_auth_response = AuthResponse(
        user=User(
            id="11111111-1111-1111-1111-111111111111",
            app_metadata={
                "provider": "email",
                "providers": ["email"],
            },
            user_metadata={},
            aud="authenticated",
            created_at=datetime.fromisoformat("2024-06-17T00:19:25.760110+00:00"),
            email="test@example.com",
        )
    )

    mock_new_user = NewUserRead(id=1, role_id=USER_ROLE_ID)

    mock_sb_sign_up.return_value = mock_auth_response
    mock_create_user.return_value = mock_new_user

    result = await sign_up(db_session, email, password)

    mock_sb_sign_up.assert_called_once_with(email, password)

    mock_create_user.assert_awaited_once_with(
        db_session,
        "11111111-1111-1111-1111-111111111111",
        USER_ROLE_ID,
    )

    assert isinstance(result, UserRead)
    assert result.id == 1
    assert result.role_id == USER_ROLE_ID
    assert result.email == email
    assert result.name is None


@patch("auth.service.sb_sign_up")
@pytest.mark.asyncio
async def test_sign_up_raises_when_supabase_returns_no_user(
    mock_sb_sign_up,
):
    """Test sign up raises 500 error when supabase returns no user."""
    db_session = MagicMock()

    mock_auth_response = AuthResponse()

    mock_sb_sign_up.return_value = mock_auth_response

    with pytest.raises(HTTPException) as exc:
        await sign_up(
            db_session,
            "test@example.com",
            "password123",
        )

    mock_sb_sign_up.assert_called_once_with("test@example.com", "password123")
    assert exc.value.status_code == 500
    assert exc.value.detail == "User detail is not returned from Supabase."
