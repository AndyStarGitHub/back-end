from __future__ import annotations

import os
from functools import lru_cache

from pydantic import (
    Field,
)
from pydantic_settings import BaseSettings, SettingsConfigDict

from app.core.config.app import AppSettings
from app.core.config.db import DBSettings
from app.core.config.redis import RedisSettings


class SecuritySettings(BaseSettings):
    JWT_SECRET: str = Field(default="dev-secret-change-me")
    JWT_ALG: str = Field(default="HS256")
    JWT_EXPIRES_MIN: int = Field(default=60)

    JWT_REFRESH_SECRET: str = "dev-refresh-secret-change-me"
    JWT_REFRESH_ALG: str = "HS256"
    JWT_REFRESH_EXPIRES_MIN: int = 7 * 24 * 60


class Auth0Settings(BaseSettings):
    DOMAIN: str
    AUDIENCE: str
    ISSUER: str
    EMAIL_CLAIM: str = "https://be-1-api/email"
    ALG: str = "RS256"
    JWKS_CACHE_SECONDS: int = 600


class Settings(BaseSettings):

    app: AppSettings = Field(default_factory=AppSettings)
    db: DBSettings = Field(default_factory=DBSettings)
    redis: RedisSettings = Field(default_factory=RedisSettings)
    security: SecuritySettings = SecuritySettings()

    model_config = SettingsConfigDict(
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    auth0: Auth0Settings = Auth0Settings(
        DOMAIN=os.getenv("AUTH0_DOMAIN", ""),
        AUDIENCE=os.getenv("AUTH0_AUDIENCE", ""),
        ISSUER=os.getenv("AUTH0_ISSUER", ""),
        EMAIL_CLAIM=os.getenv("AUTH0_EMAIL_CLAIM", "https://be-1-api/email"),
        ALG=os.getenv("AUTH0_ALG", "RS256"),
    )


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
