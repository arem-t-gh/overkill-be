from datetime import datetime
from unittest.mock import patch

import pytest
from supabase_auth.errors import AuthApiError
from supabase_auth.types import AuthResponse, User, UserResponse

from supabase_app.auth.service import get_user_by_access_token, sign_in, sign_up


@patch("supabase_app.auth.service.sb.auth.sign_up")
def test_sign_up(mock_sb_sign_up):
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

    mock_sb_sign_up.return_value = mock_response

    email = "test@example.com"
    password = "password123"

    result = sign_up(email=email, password=password)

    mock_sb_sign_up.assert_called_once_with(
        {
            "email": email,
            "password": password,
        }
    )

    assert result is mock_response


@patch("supabase_app.auth.service.sb.auth.sign_in_with_password")
def test_sign_in(mock_sb_sign_in_w_pw):
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

    mock_sb_sign_in_w_pw.return_value = mock_response

    email = "test@example.com"
    password = "password123"

    result = sign_in(email=email, password=password)

    mock_sb_sign_in_w_pw.assert_called_once_with(
        {
            "email": email,
            "password": password,
        }
    )

    assert result is mock_response


@patch("supabase_app.auth.service.sb.auth.get_user")
def test_get_user_by_access_token(mock_sb_get_user):
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

    mock_sb_get_user.return_value = mock_response

    token = "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkpvaG4gRG9lIiwiYWRtaW4iOnRydWUsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c"

    result = get_user_by_access_token(token=token)

    mock_sb_get_user.assert_called_once_with(token)

    assert result is mock_response


@patch("supabase_app.auth.service.sb.auth.get_user")
def test_get_user_by_access_token_with_invalid_token(mock_sb_get_user):
    """Test get user by access token with invalid token."""

    mock_sb_get_user.side_effect = AuthApiError(
        "invalid JWT: unable to parse or verify signature, token is malformed: token contains an invalid number of segments",
        403,
        "bad_jwt",
    )
    invalid_token = "invalid.bearer.token"
    with pytest.raises(AuthApiError) as exc_info:
        get_user_by_access_token(token=invalid_token)

    assert "invalid JWT" in str(exc_info.value)
    mock_sb_get_user.assert_called_once_with(invalid_token)
