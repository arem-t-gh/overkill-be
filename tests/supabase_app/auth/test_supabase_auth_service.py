from datetime import datetime
from unittest.mock import AsyncMock, MagicMock

import pytest
from supabase_auth.errors import AuthApiError
from supabase_auth.types import AuthResponse, User, UserResponse

from supabase_app.auth.service import (
    delete_user,
    get_user_by_access_token,
    sign_in,
    sign_up,
)


async def test_sign_up():
    """Test sign up."""

    mock_response = AuthResponse(
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

    sb_client = MagicMock()
    sb_signup_mock = AsyncMock()
    sb_signup_mock.return_value = mock_response
    sb_client.auth.sign_up = sb_signup_mock

    email = "test@example.com"
    password = "password123"

    result = await sign_up(sb_client, email=email, password=password)

    sb_signup_mock.assert_awaited_once_with({"email": email, "password": password})

    assert result is mock_response


async def test_sign_in():
    """Test sign in."""
    mock_response = AuthResponse(
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

    sb_client = MagicMock()
    sb_sign_in_w_pw_mock = AsyncMock()
    sb_sign_in_w_pw_mock.return_value = mock_response
    sb_client.auth.sign_in_with_password = sb_sign_in_w_pw_mock

    email = "test@example.com"
    password = "password123"

    result = await sign_in(sb_client, email=email, password=password)

    sb_sign_in_w_pw_mock.assert_called_once_with(
        {
            "email": email,
            "password": password,
        }
    )

    assert result is mock_response


async def test_get_user_by_access_token():
    """Test get user by access token."""
    mock_response = UserResponse(
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

    sb_client = AsyncMock()
    sb_get_user_mock = AsyncMock()
    sb_get_user_mock.return_value = mock_response
    sb_client.auth.get_user = sb_get_user_mock

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    result = await get_user_by_access_token(sb_client, token=token)

    sb_get_user_mock.assert_called_once_with(token)

    assert result is mock_response


async def test_get_user_by_access_token_with_invalid_token():
    """Test get user by access token with invalid token."""
    sb_client = AsyncMock()

    sb_client.auth.get_user.side_effect = AuthApiError(
        "invalid JWT: unable to parse or verify signature, token is malformed: token contains an invalid number of segments",
        403,
        "bad_jwt",
    )
    invalid_token = "invalid.bearer.token"
    with pytest.raises(AuthApiError) as exc_info:
        await get_user_by_access_token(sb_client, token=invalid_token)

    assert "invalid JWT" in str(exc_info.value)
    sb_client.auth.get_user.assert_called_once_with(invalid_token)


class TestDeleteUser:
    async def test_successful_delete(self):
        """Test successful delete."""

        sb_client = AsyncMock()
        mock_delete_user = AsyncMock()
        mock_delete_user.return_value = None
        sb_client.auth.admin.delete_user = mock_delete_user

        result: bool = await delete_user(
            sb_client, "11111111-1111-1111-1111-111111111111"
        )
        sb_client.auth.admin.delete_user.assert_awaited_once_with(
            "11111111-1111-1111-1111-111111111111"
        )

        assert result

    async def test_fail_delete_a_non_existent_user(self):
        """Test fail deletion of a non existent user."""
        sb_client = AsyncMock()

        sb_client.auth.admin.delete_user.side_effect = AuthApiError(
            "not found",
            404,
            "user_not_found",
        )

        # with pytest.raises(AuthApiError) as exc_info:
        result: bool = await delete_user(
            sb_client, "11111111-1111-1111-1111-111111111111"
        )
        sb_client.auth.admin.delete_user.assert_awaited_once_with(
            "11111111-1111-1111-1111-111111111111"
        )

        assert not result

    async def test_general_fail_delete(self):
        """Test fail deletion of a non existent user."""
        sb_client = AsyncMock()

        sb_client.auth.admin.delete_user.side_effect = AuthApiError(
            "unexpected failure",
            500,
            "unexpected_failure",
        )

        with pytest.raises(AuthApiError) as exc_info:
            await delete_user(sb_client, "11111111-1111-1111-1111-111111111111")

        sb_client.auth.admin.delete_user.assert_awaited_once_with(
            "11111111-1111-1111-1111-111111111111"
        )
        assert "unexpected failure" in str(exc_info.value)
