from fastapi import APIRouter
from .ping import router as ping_router
from .health import router as health_router
from app.api.users import router as users_router
from app.api.auth import router as auth_router
from app.api.auth0_me import router as auth0_me_router

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
    auth0_me_router,
    prefix="/auth0",
    tags=["auth0"]
)

__all__ = ["api_router"]
