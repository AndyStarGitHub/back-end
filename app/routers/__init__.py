from fastapi import APIRouter

from .ping import router as ping_router
from .health import router as health_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.companies import router as companies_router
from app.api.company_invitations import router as company_invitations_router
from app.api.company_members import router as company_members_router
from app.api.company_join_requests import router as company_join_requests_router


api_router = APIRouter(prefix="/api/v1")

api_router.include_router(
    health_router,
    prefix="/health",
    tags=["diagnostics"]
)
api_router.include_router(
    ping_router,
    prefix="/ping",
    tags=["diagnostics"]
)
api_router.include_router(
    users_router,
    prefix="/users",
    tags=["users"]
)
api_router.include_router(
    auth_router,
    prefix="/auth",
    tags=["auth"]
)
api_router.include_router(
    companies_router,
    prefix="/companies",
    tags=["companies"]
)
api_router.include_router(
    company_invitations_router,
    prefix="/company-invitations",
    tags=["company-invitations"]
)
api_router.include_router(
    company_members_router,
    prefix="/company-members",
    tags=["company-members"]
)
api_router.include_router(
    company_join_requests_router,
    prefix="/company-join-requests",
    tags=["company-join-requests"]
)


__all__ = ["api_router"]
