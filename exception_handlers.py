import logging

from fastapi import FastAPI, status
from fastapi.responses import JSONResponse
from sqlalchemy.exc import DBAPIError
from supabase_auth.errors import AuthApiError

logger = logging.getLogger(__name__)


async def sb_auth_api_error_handler(_, exc: AuthApiError):
    """Handle supabase auth api errors."""
    logger.warning("Supabase auth API error: %s", exc.to_dict())
    return JSONResponse(status_code=exc.status, content=exc.to_dict())


# TODO: this error return is revealing too much query details
async def sqlalchemy_dbapi_error_handler(_, exc: DBAPIError):
    """Handle sqlalchemy db api errors."""
    logger.exception("Unhandled SQLAlchemy DBAPIError", exc_info=exc)
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc.orig)},
    )


def register_exception_handlers(app: FastAPI):
    """Register exepction handlers."""
    app.add_exception_handler(AuthApiError, sb_auth_api_error_handler)  # type: ignore[reportArgumentType]

    app.add_exception_handler(DBAPIError, sqlalchemy_dbapi_error_handler)  # type: ignore[reportArgumentType]
