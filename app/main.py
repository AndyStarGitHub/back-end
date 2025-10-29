from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from app.routers import api as api_router


from app.core.config import settings
from app.services.redis_client import close_redis


@asynccontextmanager
async def lifespan(app: FastAPI):
    yield
    await close_redis()

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(api_router, prefix="/api/v1")

# if __name__ == "__main__":
#     import uvicorn
#     uvicorn.run(
#         app,
#         host=settings.HOST,
#         port=settings.PORT,
#         reload=settings.RELOAD
#     )
