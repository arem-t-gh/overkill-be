from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from db.database import get_db_session


@patch("db.database.AsyncSessionLocal")
async def test_get_db_session_yields_session(mock_async_session_local: MagicMock):
    """Test get_db_session yields a session."""
    mock_session = AsyncMock()

    mock_session.rollback = AsyncMock()

    mock_async_session_local.return_value.__aenter__.return_value = mock_session

    yielded_session = None

    session_generator = get_db_session()
    yielded_session = await anext(session_generator)

    assert yielded_session is mock_session
    mock_async_session_local.assert_called_once()
    mock_session.rollback.assert_not_called()


@patch("db.database.AsyncSessionLocal")
async def test_get_db_session_yields_error_and_call_rollback(
    mock_async_session_local: MagicMock,
):
    """Test get_db_session rollback and raise happens on error."""
    mock_session = AsyncMock()

    mock_session.rollback = AsyncMock()

    mock_async_session_local.return_value.__aenter__.return_value = mock_session

    session_generator = get_db_session()
    await anext(session_generator)

    with pytest.raises(ValueError, match="Error raised"):
        await session_generator.athrow(ValueError("Error raised"))

    mock_session.rollback.assert_called_once()
