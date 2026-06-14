from fastapi import APIRouter
from api.v1.views.supabase.auth_views import router as supabase_auth_router

router = APIRouter()
router.include_router(supabase_auth_router, prefix="/supabase")
