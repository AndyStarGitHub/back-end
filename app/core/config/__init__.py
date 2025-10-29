from __future__ import annotations
import json
from typing import List, Literal
from pydantic import (
    Field,
    SecretStr,
    computed_field,
    field_validator
)
from pydantic_settings import BaseSettings


class Settings(BaseSettings):

    ENV: Literal["dev","test","prod"] = "dev"
    DEBUG: bool = False
    LOG_LEVEL: Literal["CRITICAL","ERROR","WARNING","INFO","DEBUG"] = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    SECRET_KEY: SecretStr
    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def parse_cors(cls, v):
        if isinstance(v, str):
            s = v.strip()
            if s.startswith("["):
                try:
                    return json.loads(s)
                except Exception:
                    pass
            return [p.strip() for p in s.split(",") if p.strip()]
        return v

    DB_HOST: str = "db"
    DB_PORT: int = 5432
    DB_NAME: str = "appdb"
    DB_USER: str = "appuser"
    DB_PASSWORD: str = "apppass"

    @computed_field
    @property
    def ASYNC_DATABASE_URL(self) -> str:
        return f"postgresql+asyncpg://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    @computed_field
    @property
    def SYNC_DATABASE_URL(self) -> str:
        return f"postgresql://{self.DB_USER}:{self.DB_PASSWORD}@{self.DB_HOST}:{self.DB_PORT}/{self.DB_NAME}"

    REDIS_HOST: str = "redis"
    REDIS_PORT: int = 6379
    REDIS_DB: int = 0

    @computed_field
    @property
    def REDIS_URL(self) -> str:
        return f"redis://{self.REDIS_HOST}:{self.REDIS_PORT}/{self.REDIS_DB}"

    model_config = {
        "env_file": ".env",
        "case_sensitive": False,
        "extra": "ignore",
    }


settings = Settings()
