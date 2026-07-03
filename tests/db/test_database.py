from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.database import get_db_session

"""
Demistifying `async with get_session_factory()() as session` 
---
DB factory and the process of mocking it,

`get_session_factory` is a SYNC fn (hence mocked by MagicMock) --> inner call
...which returns the `async_sessionmaker` that returns an async context manager that we can call in SYNC fashion despite being async --> outer call
...which then finally yields the object that will be handled via `async with`

---

Here's another rough equivalent:

`async with x()() as z` can be broken down into:

def x(): # e.g. get_session_factory
    @asynccontextmanager
    async def y(): # a generator wrapped in asynccontextmanager
        yield z
    return y

inner_call = x() # SYNC call that returns y callable
outer_call = inner_call() # SYNC call that starts the `y` async context manager
z = await outer_call.__aenter__() # ASYNC call to yield. Reached `async with` at this point.

"""


@patch("db.database.get_session_factory")
async def test_get_db_session_yields_session(mock_get_session_factory: MagicMock):
    """Test get_db_session yields a session."""

    # Quick explanation
    # get_session_factory is SYNC -> MagicMock
    #   returns an async context manager which will be called in SYNC manner -> MagicMock
    #       returned value of that sync call is what will be used with `async with` -> AsyncMock

    mock_session = AsyncMock()

    mock_session.rollback = AsyncMock()
    mock_session_factory = MagicMock()

    # Notes:
    # - __aenter__() is called when entering an `async with` block
    # - So we mock that value via __aenter__.return_value
    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_get_session_factory.return_value = mock_session_factory

    yielded_session = None

    session_generator = get_db_session()
    yielded_session = await anext(session_generator)

    assert yielded_session is mock_session
    mock_get_session_factory.assert_called_once()
    mock_session.rollback.assert_not_called()


@patch("db.database.get_session_factory")
async def test_get_db_session_yields_error_and_call_rollback(
    mock_get_session_factory: MagicMock,
):
    """Test get_db_session rollback and raise happens on error."""
    mock_session = AsyncMock()

    mock_session.rollback = AsyncMock()

    mock_session_factory = MagicMock()

    mock_session_factory.return_value.__aenter__.return_value = mock_session

    mock_get_session_factory.return_value = mock_session_factory

    session_generator = get_db_session()
    await anext(session_generator)

    with pytest.raises(ValueError, match="Error raised"):
        await session_generator.athrow(ValueError("Error raised"))

    mock_session.rollback.assert_called_once()
