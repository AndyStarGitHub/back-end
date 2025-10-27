from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import api as api_router


from app.core.config import app_settings, db_settings
from app.services.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=app_settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        app,
        host=db_settings.HOST,
        port=db_settings.PORT,
        reload=db_settings.RELOAD
    )
