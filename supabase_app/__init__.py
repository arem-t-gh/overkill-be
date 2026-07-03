from typing import Annotated

from fastapi import Depends
from supabase import AsyncClient, acreate_client

from config import SUPABASE_KEY, SUPABASE_URL


async def get_supabase_client():
    """Get supabase async client."""
    return await acreate_client(SUPABASE_URL, SUPABASE_KEY)


SBClient = Annotated[AsyncClient, Depends(get_supabase_client)]
