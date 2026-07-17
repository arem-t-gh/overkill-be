import uuid
from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException

from role.constants import ADMIN_ROLE_ID, USER_ROLE_ID
from user.models import User, UserUpdate
from user.service import (
    create_user,
    delete_user_via_external_auth_id,
    get_user_by_external_auth_id,
    update_user,
)


class TestCreateUserIntegration:
    async def test_creates_and_persists_user_row(self, db_session):
        external_auth_id = str(uuid.uuid4())

        result = await create_user(db_session, external_auth_id=external_auth_id)

        assert result.role_id == USER_ROLE_ID

        persisted = await db_session.get(User, result.id)
        assert persisted is not None
        assert persisted.external_auth_id == uuid.UUID(external_auth_id)
        assert persisted.role_id == USER_ROLE_ID

    async def test_respects_explicit_role_id(self, db_session):
        result = await create_user(
            db_session, external_auth_id=str(uuid.uuid4()), role_id=ADMIN_ROLE_ID
        )

        persisted = await db_session.get(User, result.id)
        assert persisted.role_id == ADMIN_ROLE_ID


class TestGetUserByExternalAuthIdIntegration:
    async def test_finds_a_previously_created_user(self, db_session):
        external_auth_id = str(uuid.uuid4())
        created = await create_user(db_session, external_auth_id=external_auth_id)

        found = await get_user_by_external_auth_id(db_session, external_auth_id)

        assert found is not None
        assert found.id == created.id
        assert found.external_auth_id == uuid.UUID(external_auth_id)

    async def test_returns_none_for_an_unknown_id(self, db_session):
        found = await get_user_by_external_auth_id(db_session, str(uuid.uuid4()))

        assert found is None


class TestUpdateUserIntegration:
    async def test_updates_name_and_persists_the_change(self, db_session):
        created = await create_user(db_session, external_auth_id=str(uuid.uuid4()))

        result = await update_user(
            db_session, created.id, UserUpdate(name="Ada Lovelace")
        )

        assert result.name == "Ada Lovelace"

        persisted = await db_session.get(User, created.id)
        assert persisted.name == "Ada Lovelace"

    async def test_raises_404_when_user_does_not_exist(self, db_session):
        with pytest.raises(HTTPException) as exc_info:
            await update_user(db_session, 999_999, UserUpdate(name="Nobody"))

        assert exc_info.value.status_code == 404


class TestDeleteUserViaExternalAuthIdIntegration:
    @patch("user.service.sb_delete_user", new_callable=AsyncMock)
    async def test_deletes_the_user_row_when_supabase_delete_succeeds(
        self, sb_delete_user, db_session
    ):
        sb_delete_user.return_value = True
        external_auth_id = str(uuid.uuid4())
        created = await create_user(db_session, external_auth_id=external_auth_id)

        result = await delete_user_via_external_auth_id(
            db_session, MagicMock(), external_auth_id
        )

        assert result is True
        assert await db_session.get(User, created.id) is None

    @patch("user.service.sb_delete_user", new_callable=AsyncMock)
    async def test_returns_false_when_user_is_in_neither_supabase_nor_the_db(
        self, sb_delete_user, db_session
    ):
        sb_delete_user.return_value = False

        result = await delete_user_via_external_auth_id(
            db_session, MagicMock(), str(uuid.uuid4())
        )

        assert result is False
