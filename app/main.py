import logging

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager

from starlette.requests import Request
from starlette.responses import JSONResponse

from app.core.config import settings
from app.core.error_handlers import register_exception_handlers
from app.core.errors import NotFound, Conflict
from app.services.redis_client import close_redis
from app.routers import api_router

from loguru import logger

logger.add("log/meduzzen.log")
logger.debug("That's it, beautiful and simple logging!")


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()


# setup_logging()
# app/main.py (на самому початку файлу, до створення app)
# import logging, sys

# logging.basicConfig(
#     level=logging.INFO,  # або DEBUG
#     format="%(levelname)s %(asctime)s %(name)s: %(message)s",
#     stream=sys.stdout,
# )

# додатково, щоб наші логери точно не губилися
# logging.getLogger("app").setLevel(logging.DEBUG)
# logging.getLogger("app.auth").setLevel(logging.DEBUG)

app = FastAPI()
register_exception_handlers(app)
app.include_router(api_router)


app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.app.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.exception_handler(NotFound)
async def not_found_handler(request: Request, exc: NotFound):
    return JSONResponse(
        status_code=404,
        content={"detail": str(exc) or "Not found"}
    )


@app.exception_handler(Conflict)
async def conflict_handler(request: Request, exc: Conflict):
    return JSONResponse(
        status_code=409,
        content={"detail": str(exc) or "Conflict"}
    )

if __name__ == "__main__":
    import uvicorn
    from app.core.config import settings

    uvicorn.run(
        "app.main:app",
        host=settings.app.HOST,
        port=settings.app.PORT,
        reload=settings.app.RELOAD,
    )
