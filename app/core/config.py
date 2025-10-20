from functools import lru_cache
from typing import Literal, Optional

from pydantic import SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    APP_NAME: str = "Meduzzen BE-1"
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

    DATABASE_URL: Optional[str] = None

    HOST: str = "0.0.0.0"
    PORT: int = 8000

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
    )

    @field_validator("LOG_LEVEL", mode="before")
    @classmethod
    def normalize_log_level(cls, val: str) -> str:
        return str(val).upper()

    @model_validator(mode="after")
    def check_secret_key(self) -> "Settings":
        placeholder_values = {
            "",
            "change_me",
            "CHANGE_ME",
            "REPLACE_WITH_SECURE_RANDOM",
        }
        if self.ENV == "prod":
            if (sk := self.SECRET_KEY.get_secret_value()) in placeholder_values:
                raise ValueError(
                    "SECRET_KEY must be a strong, non-default value in production"
                )
        return self


@lru_cache
def get_settings() -> Settings:
    return Settings()


settings = get_settings()
