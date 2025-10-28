from __future__ import annotations
from pydantic_settings import BaseSettings
from pydantic import Field


class DBSettings(BaseSettings):
    HOST: str = "db"
    PORT: int = 5432
    NAME: str = "appdb"
    USER: str = "appuser_"
    PASSWORD: str = "apppass_"

    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql+psycopg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    model_config = {
        "env_prefix": "DB_",
        "extra": "ignore",
    }
