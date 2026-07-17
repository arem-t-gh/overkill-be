from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch

from supabase_auth.types import (
    AuthResponse,
    Session,
    User as SupabaseUser,
)

from auth.service import sign_in, sign_up
from role.constants import USER_ROLE_ID
from user.models import User
from user.service import create_user


def _supabase_user(external_auth_id: str, email: str) -> SupabaseUser:
    return SupabaseUser(
        id=external_auth_id,
        app_metadata={"provider": "email", "providers": ["email"]},
        user_metadata={},
        aud="authenticated",
        created_at=datetime.fromisoformat("2024-06-17T00:19:25.760110+00:00"),
        email=email,
    )


class TestSignUpIntegration:
    @patch("auth.service.sb_sign_up", new_callable=AsyncMock)
    async def test_creates_a_real_user_row_in_postgres(self, sb_sign_up, db_session):
        external_auth_id = "22222222-2222-2222-2222-222222222222"
        email = "integration-signup@example.com"
        sb_sign_up.return_value = AuthResponse(
            user=_supabase_user(external_auth_id, email)
        )

        result = await sign_up(db_session, MagicMock(), email, "password123")

        assert result.email == email
        assert result.role_id == USER_ROLE_ID

        persisted = await db_session.get(User, result.id)
        assert persisted is not None
        assert str(persisted.external_auth_id) == external_auth_id


class TestSignInIntegration:
    @patch("auth.service.sb_sign_in", new_callable=AsyncMock)
    async def test_creates_local_user_row_on_first_sign_in(
        self, sb_sign_in, db_session
    ):
        external_auth_id = "33333333-3333-3333-3333-333333333333"
        email = "integration-signin@example.com"
        sb_user = _supabase_user(external_auth_id, email)
        sb_sign_in.return_value = AuthResponse(
            user=sb_user,
            session=Session(
                access_token="access-token",
                refresh_token="refresh-token",
                expires_in=3600,
                token_type="bearer",
                user=sb_user,
            ),
        )

        result = await sign_in(db_session, MagicMock(), email, "password123")

        assert result.access_token == "access-token"
        persisted = await db_session.get(User, result.id)
        assert persisted is not None
        assert str(persisted.external_auth_id) == external_auth_id

    @patch("auth.service.sb_sign_in", new_callable=AsyncMock)
    async def test_reuses_the_existing_local_row_instead_of_duplicating_it(
        self, sb_sign_in, db_session
    ):
        external_auth_id = "44444444-4444-4444-4444-444444444444"
        email = "integration-existing@example.com"
        created = await create_user(db_session, external_auth_id=external_auth_id)

        sb_user = _supabase_user(external_auth_id, email)
        sb_sign_in.return_value = AuthResponse(
            user=sb_user,
            session=Session(
                access_token="access-token-2",
                refresh_token="refresh-token-2",
                expires_in=3600,
                token_type="bearer",
                user=sb_user,
            ),
        )

        result = await sign_in(db_session, MagicMock(), email, "password123")

        assert result.id == created.id
