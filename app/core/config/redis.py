from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class RedisSettings(BaseSettings):

    HOST: str = "redis"
    PORT: int = 6379
    DB: int = 0

    model_config = SettingsConfigDict(
        env_prefix="REDIS_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def URL(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"
