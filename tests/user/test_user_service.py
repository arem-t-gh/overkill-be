from unittest.mock import AsyncMock, MagicMock, patch

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from role.constants import USER_ROLE_ID
from user.models import NewUserRead, UserRead
from user.service import create_user, get_user_by_external_auth_id


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
    return session


@pytest.fixture
def mock_user():
    """Mock user fixture.

    Using MagicMock instead of a real User instance keeps the test
    independent of the ORM schema — if columns are added/removed, these
    tests don't break unless the service logic itself changes.
    """
    user = MagicMock()
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
        expected = MagicMock(spec=UserRead)

        with patch(
            "user.service.UserRead.model_validate", return_value=expected
        ) as mock_validate:
            result = await get_user_by_external_auth_id(db_session, "ext-auth-id")

        mock_validate.assert_called_once_with(mock_user)
        assert result is expected

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
