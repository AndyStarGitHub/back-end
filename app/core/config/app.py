from __future__ import annotations
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Literal


class AppSettings(BaseSettings):

    APP_NAME: str = "Meduzzen FastAPI Best Practice"
    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = True
    LOG_LEVEL: Literal["CRITICAL", "ERROR", "WARNING", "INFO", "DEBUG"] = "INFO"

    HOST: str = "0.0.0.0"
    PORT: int = 8000
    RELOAD: bool = True

    CORS_ORIGINS: list[str] = Field(default_factory=lambda: ["*"])

    QUIZ_IMPORT_MAX_ROWS: int = 5000

    model_config = SettingsConfigDict(
        env_prefix="APP_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )
