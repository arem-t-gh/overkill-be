from fastapi import APIRouter, status
from fastapi.responses import JSONResponse

from api.v1.user.schemas import UserUpdateRequest
from db.database import DBSession
from supabase_app import SBClient
from user.models import UserRead, UserUpdate
from user.service import (
    delete_user_via_external_auth_id as delete_user_service,
    update_user as update_user_service,
)

router = APIRouter()


@router.patch("/{user_id}")
async def update_user(
    db_session: DBSession,
    # TODO: admin only
    # _: Annotated[UserRead, Depends(AuthorizedCurrentUser([ADMIN_ROLE_ID]))],
    user_id: int,
    request: UserUpdateRequest,
) -> UserRead:
    """Update user."""
    details = UserUpdate(**request.model_dump())

    user = await update_user_service(db_session, user_id, details)

    return user


@router.delete("/{external_auth_id}")
async def delete_user(
    db_session: DBSession,
    sb_client: SBClient,
    # TODO: admin only
    # _: Annotated[UserRead, Depends(AuthorizedCurrentUser([ADMIN_ROLE_ID]))],
    external_auth_id: str,
) -> JSONResponse:
    """Update user."""
    delete_status = await delete_user_service(db_session, sb_client, external_auth_id)

    if delete_status:
        return JSONResponse(
            content={
                "message": f"User w/ external auth id {external_auth_id} has been deleted."
            },
            status_code=status.HTTP_200_OK,
        )
    else:
        return JSONResponse(
            content={
                "message": f"User w/ external auth id {external_auth_id} is not found."
            },
            status_code=status.HTTP_404_NOT_FOUND,
        )
