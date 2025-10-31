from fastapi import APIRouter
from .ping import router as ping_router
from .health import router as health_router  # якщо є health

api = APIRouter()

api.include_router(health_router, prefix="/health", tags=["diagnostics"])
api.include_router(ping_router,   prefix="/ping",   tags=["diagnostics"])
