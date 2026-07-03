from unittest.mock import ANY, AsyncMock, MagicMock, patch

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient
from sqlalchemy.exc import DBAPIError
from supabase_auth.errors import AuthApiError

from api.router_handler import register_routers
from api.v1.auth.views import get_current_user
from db.database import get_db_session
from exception_handlers import register_exception_handlers
from role.constants import USER_ROLE_ID
from supabase_app import get_supabase_client
from user.models import UserRead


# If callable is a fixture, pytest executes it already once it enters the test.
# So for fixtures that are expected to be callable, then the return should be a callable as well
@pytest.fixture
async def mock_db_session_dependency():
    """Mock db dependency."""

    async def _override():
        yield MagicMock()

    return _override


@pytest.fixture
async def mock_supabase_client_dependency():
    """Mock supabase client deepndency"""

    async def _override():
        yield MagicMock()

    return _override


async def create_test_app():
    """App factory."""
    app = FastAPI()

    register_routers(app)
    register_exception_handlers(app)

    return app


async def test_auth_api_error_handler():
    """Test AuthApiError hanlder."""
    app = await create_test_app()

    @app.get("/test")
    def route():
        raise AuthApiError(
            message="Invalid credentials",
            status=401,
            code="invalid_credentials",
        )

    client = TestClient(app)

    response = client.get("/test")

    assert response.status_code == 401
    assert response.json()["message"] == "Invalid credentials"


async def test_dbapi_error_handler_clean():
    """Test DBAPIError handler."""

    app = await create_test_app()

    @app.get("/test")
    def route():
        raise DBAPIError(
            statement="SELECT 1",
            params={},
            orig=Exception("connection failed"),
        )

    client = TestClient(app)

    response = client.get("/test")

    assert response.status_code == 500
    assert response.json()["detail"] == "connection failed"


async def test_home():
    """Test home."""
    app = await create_test_app()

    client = TestClient(app)

    response = client.get("/")

    assert response.status_code == 200
    assert response.json() == 200


api_v1_auth_prefix = "/api/v1/auth"


async def test_current_user_returns_user():
    """Test current user returns user."""
    app = await create_test_app()

    client = TestClient(app)

    async def override_get_current_user():
        return UserRead(
            id=1,
            role_id=USER_ROLE_ID,
            email="test@example.com",
        )

    app.dependency_overrides[get_current_user] = override_get_current_user

    response = client.get(api_v1_auth_prefix + "/current-user")
    response_json = response.json()

    assert response.status_code == 200
    assert response_json["id"] == 1
    assert response_json["role_id"] == USER_ROLE_ID
    assert response_json["email"] == "test@example.com"

    app.dependency_overrides.clear()


@patch("api.v1.auth.views.auth_sign_up", new_callable=AsyncMock)
async def test_successful_sign_up_returns_user(
    mock_auth_sign_up, mock_db_session_dependency, mock_supabase_client_dependency
):
    """Test succesful sign up returns user."""
    app = await create_test_app()
    app.dependency_overrides[get_db_session] = mock_db_session_dependency
    app.dependency_overrides[get_supabase_client] = mock_supabase_client_dependency

    client = TestClient(app)

    mock_auth_sign_up.return_value = UserRead(
        id=1, role_id=USER_ROLE_ID, email="test@example.com"
    )
    payload = {"email": "test@example.com", "password": "test123"}

    response = client.post(api_v1_auth_prefix + "/sign-up", json=payload)
    response_json = response.json()

    mock_auth_sign_up.assert_awaited_once_with(
        # By then, dependencies have yielded/returned whatever they will return which fastapi resolves internally.
        # Pass in ANY to simulate those interanlly resolved values.
        ANY,
        ANY,
        "test@example.com",
        "test123",
    )

    assert response.status_code == 200
    assert response_json["id"] == 1
    assert response_json["role_id"] == USER_ROLE_ID
    assert response_json["email"] == "test@example.com"

    app.dependency_overrides.clear()
