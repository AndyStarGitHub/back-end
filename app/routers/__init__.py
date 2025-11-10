from fastapi import APIRouter
from .ping import router as ping_router
from .health import router as health_router
from app.api.users import router as users_router

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

__all__ = ["api_router"]
