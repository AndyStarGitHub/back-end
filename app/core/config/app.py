from __future__ import annotations
from pydantic import Field, SecretStr
from pydantic_settings import BaseSettings
from typing import Literal


class AppSettings(BaseSettings):
    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    SECRET_KEY: SecretStr

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    model_config = {
        "env_prefix": "APP_",
        "extra": "ignore",
    }
