from typing import Literal

from fastapi import FastAPI

from api.v1.router import router as api_v1_router


def register_routers(app: FastAPI):
    """Register routers."""

    @app.get("/")
    async def home() -> Literal[200]:
        """Home endpoint."""
        return 200

    app.include_router(api_v1_router, prefix="/api/v1")
