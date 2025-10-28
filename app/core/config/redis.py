from __future__ import annotations
from pydantic_settings import BaseSettings


class RedisSettings(BaseSettings):
    HOST: str = "redis"
    PORT: int = 6379
    DB: int = 0

    @property
    def URL(self) -> str:
        return f"redis://{self.HOST}:{self.PORT}/{self.DB}"

    model_config = {
        "env_prefix": "REDIS_",
        "extra": "ignore",
    }
