from typing import Literal

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from supabase_auth.errors import AuthApiError

from api.v1.router import router as api_v1_router

app = FastAPI(title="Overkill")


# TODO: move this elsewhere
@app.exception_handler(AuthApiError)
async def sb_auth_api_error_handler(_, exc: AuthApiError):
    """Handle supabase auth api errors."""
    return JSONResponse(status_code=exc.status, content=exc.to_dict())


@app.exception_handler(DBAPIError)
async def sqlalchemy_dbapi_error_handler(_, exc: DBAPIError):
    """Handle sqlalchemy db api errors."""
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc.orig)},
    )


@app.get("/")
async def home() -> Literal[200]:
    """Home endpoint."""
    return 200


app.include_router(api_v1_router, prefix="/api/v1")
