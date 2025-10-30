from __future__ import annotations

from functools import lru_cache

from pydantic import (
    Field,
    SecretStr,
    computed_field,
    field_validator
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.app import AppSettings
from app.core.config.db import DBSettings
from app.core.config.redis import RedisSettings


class Settings(BaseSettings):

    app: AppSettings = Field(default_factory=AppSettings)
    db: DBSettings = Field(default_factory=DBSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
