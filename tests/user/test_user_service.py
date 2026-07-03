from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from supabase import AsyncClient

from role.constants import USER_ROLE_ID
from user.models import NewUserRead, User, UserRead, UserUpdate
from user.service import (
    create_user,
    delete_user_via_external_auth_id,
    get_user_by_external_auth_id,
    update_user,
)


@pytest.fixture
def db_session():
    """DB session fixture.

    - add()    → sync MagicMock  (SQLAlchemy's session.add is not a coroutine)
    - commit() → AsyncMock       (awaited in the service)
    - execute() → AsyncMock      (awaited in the service)

    We don't spin up a real engine here. Unit tests should be fast and
    isolated; the real DB wiring (engine, pool, get_db_session) is covered
    by integration tests.
    """
    session = AsyncMock(spec=AsyncSession)
    session.add = MagicMock()  # sync
    session.commit = AsyncMock()  # async
    session.execute = AsyncMock()  # async
    session.delete = AsyncMock()  # async
    return session


@pytest.fixture
def mock_user():
    """Mock user fixture.

    Using MagicMock instead of a real User instance keeps the test
    independent of the ORM schema — if columns are added/removed, these
    tests don't break unless the service logic itself changes.
    """
    user = MagicMock(spec=User)
    user.id = 1
    user.external_auth_id = "ext-auth-id"
    user.role_id = USER_ROLE_ID
    return user


class TestCreateUser:
    """Test create user.
    What we care about:
      1. A User object is constructed with the right fields and handed to session.add().
      2. commit() is awaited (the write actually happens).
      3. The committed object is passed to NewUserRead.model_validate().
      4. role_id defaults to USER_ROLE_ID but can be overridden.

    What we deliberately do NOT test here:
      - That SQLAlchemy actually persists the row (integration concern).
      - Pydantic validation logic inside NewUserRead (unit-tested in model tests).
    """

    async def test_adds_user_with_correct_fields(self, db_session):
        """Test add user w/ correct fields."""
        with patch(
            "user.service.NewUserRead.model_validate",
            return_value=MagicMock(spec=NewUserRead),
        ):
            await create_user(db_session, external_auth_id="ext-auth-id")

        db_session.add.assert_called_once()
        added_user = db_session.add.call_args[0][0]
        assert added_user.external_auth_id == "ext-auth-id"
        assert added_user.role_id == USER_ROLE_ID

    async def test_default_role_is_user_role(self, db_session):
        """Test default role is assumed when not supplied."""
        with patch(
            "user.service.NewUserRead.model_validate",
            return_value=MagicMock(spec=NewUserRead),
        ):
            await create_user(db_session, external_auth_id="ext-auth-id")

        added_user = db_session.add.call_args[0][0]
        assert added_user.role_id == USER_ROLE_ID

    async def test_passed_role_is_respected(self, db_session):
        """Test passing a different role is recognized."""
        with patch(
            "user.service.NewUserRead.model_validate",
            return_value=MagicMock(spec=NewUserRead),
        ):
            await create_user(db_session, external_auth_id="ext-auth-id", role_id=42)

        added_user = db_session.add.call_args[0][0]
        assert added_user.role_id == 42

    async def test_commit_is_awaited(self, db_session):
        """Test commit is awaited."""
        with patch(
            "user.service.NewUserRead.model_validate",
            return_value=MagicMock(spec=NewUserRead),
        ):
            await create_user(db_session, external_auth_id="ext-auth-id")

        db_session.commit.assert_awaited_once()

    async def test_model_validate_called_after_commit(self, db_session):
        """Test order of commit and validate is in order."""
        order = []
        db_session.commit.side_effect = lambda: order.append("commit")

        with patch(
            "user.service.NewUserRead.model_validate",
            side_effect=lambda u: (
                order.append("validate") or MagicMock(spec=NewUserRead)
            ),
        ):
            await create_user(db_session, external_auth_id="ext-auth-id")

        assert order == ["commit", "validate"], (
            "model_validate must be called after commit; "
            "expire_on_commit=False makes this safe, but the order still matters."
        )


class TestGetUserByExternalAuthId:
    """Test get user by external auth id.
    What we care about:
      1. The SELECT filters on external_auth_id (not some other column).
      2. When a row exists → returns UserRead.model_validate(user).
      3. When no row exists → returns None, not an exception.

    What we deliberately do NOT test:
      - That the SQL reaches the DB (integration concern).
      - Pydantic validation inside UserRead.
    """

    def _make_execute_result(self, db_session, user_or_none):
        """Fake scalar result helper."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user_or_none
        db_session.execute.return_value = mock_result

    async def test_returns_user_read_when_found(self, db_session, mock_user):
        """Test user is returned when found."""
        self._make_execute_result(db_session, mock_user)

        result = await get_user_by_external_auth_id(db_session, "ext-auth-id")

        assert result is mock_user

    async def test_returns_none_when_not_found(self, db_session):
        """Test none is returned when not found."""
        self._make_execute_result(db_session, None)

        result = await get_user_by_external_auth_id(db_session, "invalid-id")

        assert result is None

    async def test_query_filters_on_external_auth_id(self, db_session):
        """Test external auth id is used in where clause."""
        self._make_execute_result(db_session, None)

        await get_user_by_external_auth_id(db_session, "ext-auth-id")

        db_session.execute.assert_awaited_once()
        statement = db_session.execute.call_args[0][0]
        assert "external_auth_id" in str(statement.whereclause)

    async def test_execute_is_awaited(self, db_session):
        """Test execute is awaited."""
        self._make_execute_result(db_session, None)

        await get_user_by_external_auth_id(db_session, "invalid-id")

        db_session.execute.assert_awaited_once()


class TestUpdateUser:
    @patch("user.service.get_user_by_id", new_callable=AsyncMock)
    async def test_successful_update(self, get_user_by_id, db_session):
        """Test update is successful."""
        mock_user_orm = User(
            id=1,
            external_auth_id="11111111-1111-1111-1111-111111111111",
            role_id=USER_ROLE_ID,
            name="Ada Lovelace",
        )

        expected_result = UserRead(id=1, role_id=USER_ROLE_ID, name="Charles Babbage")
        update_details = UserUpdate(name="Charles Babbage")

        get_user_by_id.return_value = mock_user_orm

        result = await update_user(db_session, 1, update_details)

        get_user_by_id.assert_awaited_once_with(db_session, 1)
        assert result == expected_result

    @patch("user.service.get_user_by_id", new_callable=AsyncMock)
    async def test_user_not_found(self, get_user_by_id, db_session):
        """Test user to update is not found."""

        get_user_by_id.return_value = None
        update_details = UserUpdate(name="Charles Babbage")
        with pytest.raises(HTTPException) as exc_info:
            await update_user(db_session, 1, update_details)

        get_user_by_id.assert_awaited_once_with(db_session, 1)
        assert "User is not found." in str(exc_info.value)


@pytest.fixture
def sb_client():
    """Supabase client fixture."""
    return AsyncMock(spec=AsyncClient)


class TestDeleteUser:
    @patch("user.service.get_user_by_external_auth_id", new_callable=AsyncMock)
    @patch("user.service.sb_delete_user", new_callable=AsyncMock)
    async def test_successful_delete_user_via_external_auth_id(
        self, sb_delete_user, get_user_by_external_auth_id, db_session, sb_client
    ):
        """Test successful delete for delete_user_via_external_auth_id."""

        external_auth_id = "11111111-1111-1111-1111-111111111111"
        mock_user_orm = User(
            id=1,
            external_auth_id=external_auth_id,
            role_id=USER_ROLE_ID,
            name="Ada Lovelace",
        )

        get_user_by_external_auth_id.return_value = mock_user_orm

        result: bool = await delete_user_via_external_auth_id(
            db_session, sb_client, external_auth_id
        )

        sb_delete_user.assert_awaited_once_with(sb_client, external_auth_id)
        get_user_by_external_auth_id.assert_awaited_once_with(
            db_session, external_auth_id
        )

        assert result


class TestGetUser:
    def _make_execute_result(self, db_session, user_or_none):
        """Fake scalar result helper."""
        mock_result = MagicMock()
        mock_result.scalar_one_or_none.return_value = user_or_none
        db_session.execute.return_value = mock_result

    async def test_successful_get(self, db_session, mock_user):
        self._make_execute_result(db_session, mock_user)

        result = await get_user_by_external_auth_id(
            db_session, "11111111-1111-1111-1111-111111111111"
        )

        assert result is mock_user
