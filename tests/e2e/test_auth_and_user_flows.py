from datetime import datetime
from unittest.mock import AsyncMock, patch

from supabase_auth.types import (
    AuthResponse,
    User as SupabaseUser,
    UserResponse,
)

from role.constants import USER_ROLE_ID

AUTH_PREFIX = "/api/v1/auth"
USER_PREFIX = "/api/v1/user"


def _supabase_user(external_auth_id: str, email: str) -> SupabaseUser:
    return SupabaseUser(
        id=external_auth_id,
        app_metadata={"provider": "email", "providers": ["email"]},
        user_metadata={},
        aud="authenticated",
        created_at=datetime.fromisoformat("2024-06-17T00:19:25.760110+00:00"),
        email=email,
    )


class TestSignUpThenFetchCurrentUserE2E:
    @patch("auth.service.get_user_by_access_token", new_callable=AsyncMock)
    @patch("auth.service.sb_sign_up", new_callable=AsyncMock)
    async def test_signed_up_user_is_retrievable_via_current_user(
        self, sb_sign_up, get_user_by_access_token, client
    ):
        """Sign up over HTTP, land the row in real Postgres, then read it back over HTTP."""
        external_auth_id = "aaaaaaaa-aaaa-aaaa-aaaa-aaaaaaaaaaaa"
        email = "e2e-signup@example.com"

        sb_sign_up.return_value = AuthResponse(
            user=_supabase_user(external_auth_id, email)
        )

        sign_up_response = await client.post(
            f"{AUTH_PREFIX}/sign-up",
            json={"email": email, "password": "password123"},
        )

        assert sign_up_response.status_code == 200
        created_user = sign_up_response.json()
        assert created_user["email"] == email
        assert created_user["role_id"] == USER_ROLE_ID

        get_user_by_access_token.return_value = UserResponse(
            user=_supabase_user(external_auth_id, email)
        )

        current_user_response = await client.get(
            f"{AUTH_PREFIX}/current-user",
            headers={"Authorization": "Bearer fake-access-token"},
        )

        assert current_user_response.status_code == 200
        fetched_user = current_user_response.json()
        assert fetched_user["id"] == created_user["id"]
        assert fetched_user["role_id"] == USER_ROLE_ID


class TestUpdateUserE2E:
    @patch("auth.service.sb_sign_up", new_callable=AsyncMock)
    async def test_updating_a_user_persists_the_new_name(self, sb_sign_up, client):
        """Create a user over HTTP, update it over HTTP, and confirm the change sticks."""
        external_auth_id = "bbbbbbbb-bbbb-bbbb-bbbb-bbbbbbbbbbbb"
        email = "e2e-update@example.com"
        sb_sign_up.return_value = AuthResponse(
            user=_supabase_user(external_auth_id, email)
        )

        sign_up_response = await client.post(
            f"{AUTH_PREFIX}/sign-up",
            json={"email": email, "password": "password123"},
        )
        created_user = sign_up_response.json()

        update_response = await client.patch(
            f"{USER_PREFIX}/{created_user['id']}",
            json={"name": "Ada Lovelace"},
        )

        assert update_response.status_code == 200
        assert update_response.json()["name"] == "Ada Lovelace"

        missing_response = await client.patch(
            f"{USER_PREFIX}/999999999",
            json={"name": "Nobody"},
        )
        assert missing_response.status_code == 404


class TestDeleteUserE2E:
    @patch("user.service.sb_delete_user", new_callable=AsyncMock)
    @patch("auth.service.sb_sign_up", new_callable=AsyncMock)
    async def test_deleting_a_user_removes_it_and_repeat_delete_is_not_found(
        self, sb_sign_up, sb_delete_user, client
    ):
        """Create a user over HTTP, delete it over HTTP, and confirm it's really gone."""
        external_auth_id = "cccccccc-cccc-cccc-cccc-cccccccccccc"
        email = "e2e-delete@example.com"
        sb_sign_up.return_value = AuthResponse(
            user=_supabase_user(external_auth_id, email)
        )
        await client.post(
            f"{AUTH_PREFIX}/sign-up",
            json={"email": email, "password": "password123"},
        )

        sb_delete_user.return_value = True
        delete_response = await client.delete(f"{USER_PREFIX}/{external_auth_id}")

        assert delete_response.status_code == 200
        assert "has been deleted" in delete_response.json()["message"]

        sb_delete_user.return_value = False
        repeat_delete_response = await client.delete(
            f"{USER_PREFIX}/{external_auth_id}"
        )

        assert repeat_delete_response.status_code == 404
