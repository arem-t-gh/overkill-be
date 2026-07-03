from unittest.mock import AsyncMock, patch

from config import SUPABASE_KEY, SUPABASE_URL
from supabase_app import get_supabase_client


@patch("supabase_app.acreate_client", new_callable=AsyncMock)
async def test_get_supabase_client_returns_client(mock_acreate_client: AsyncMock):
    """Test get supabase async client returns client."""
    mock_client = AsyncMock()
    mock_acreate_client.return_value = mock_client

    sb_client = await get_supabase_client()

    assert sb_client is mock_client
    mock_acreate_client.assert_awaited_once_with(SUPABASE_URL, SUPABASE_KEY)
