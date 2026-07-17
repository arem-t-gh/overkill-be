from typing import AsyncGenerator
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from httpx import ASGITransport, AsyncClient

from api.router_handler import register_routers
from db.database import get_db_session
from exception_handlers import register_exception_handlers
from supabase_app import get_supabase_client


@pytest.fixture
async def app(db_session) -> FastAPI:
    """Full app wired to the real, per-test-isolated `db_session`.

    Only the third-party Supabase client is stubbed out (no live Supabase
    project is available in tests); individual tests patch the specific
    `sb_*` calls they exercise, same as the existing view-level unit tests.
    """
    application = FastAPI()
    register_routers(application)
    register_exception_handlers(application)

    async def _override_get_db_session():
        yield db_session

    async def _override_get_supabase_client():
        return MagicMock()

    application.dependency_overrides[get_db_session] = _override_get_db_session
    application.dependency_overrides[get_supabase_client] = (
        _override_get_supabase_client
    )

    return application


@pytest.fixture
async def client(app: FastAPI) -> AsyncGenerator[AsyncClient, None]:
    """Async HTTP client driving the app in-process over ASGI.

    Why ASGITransport not TestClient?

    TestClient spawns a new thread (with its own event loop) for every request.
    If a DB connection was already opened on a different loop (e.g. by a prior
    fixture), using it from that request would raise a RuntimeError -- asyncpg
    connections are bound to the loop that created them and can't be reused
    from another one.

    ASGITransport instead runs the request on the same event loop that's
    already running the test, so a DB connection opened by a prior fixture
    (like db_session) stays on that same loop the whole way through.

    That's why TestClient is fine for unit tests

    """
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as ac:
        yield ac
