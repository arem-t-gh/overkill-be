from fastapi import APIRouter
from api.v1.views.auth_views import router as auth_router

router = APIRouter()

router.include_router(auth_router, prefix="/auth")
