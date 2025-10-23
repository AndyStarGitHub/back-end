from functools import lru_cache
from typing import Literal, List
from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
import json


class Settings(BaseSettings):
    APP_NAME: str = "Meduzzen FastAPI Best Practice"
    ENV: Literal["dev", "test", "prod"] = "dev"
    DEBUG: bool = False
    LOG_LEVEL: Literal[
        "CRITICAL",
        "ERROR",
        "WARNING",
        "INFO",
        "DEBUG"
    ] = "INFO"

    SECRET_KEY: SecretStr

    DATABASE_URL: str
    REDIS_URL: str

    CORS_ORIGINS: List[str] = Field(default_factory=lambda: ["*"])

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore"
    )

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def _normalize_log_level(cls, v: str) -> str:
        return str(v).upper()

    @field_validator("CORS_ORIGINS", mode="before")
    @classmethod
    def _parse_cors(cls, v):
        if isinstance(v, str):
            v = v.strip()
            if not v:
                return ["*"]
            if v.startswith("["):
                return json.loads(v)
            return [s.strip() for s in v.split(",") if s.strip()]
        return v

    @model_validator(mode="after")
    def _check_secret_key(self) -> "Settings":
        bad = {"", "change_me", "CHANGE_ME", "REPLACE_WITH_SECURE_RANDOM"}
        if self.ENV == "prod" and self.SECRET_KEY.get_secret_value() in bad:
            raise ValueError(
                "SECRET_KEY must be a strong, non-default value in production"
            )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
