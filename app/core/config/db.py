from __future__ import annotations
from pydantic_settings import BaseSettings, SettingsConfigDict


class DBSettings(BaseSettings):

    HOST: str = "db"
    PORT: int = 5432
    NAME: str = "appdb"
    USER: str = "appuser"
    PASSWORD: str = "apppass"

    model_config = SettingsConfigDict(
        env_prefix="DB_",
        env_file=".env",
        extra="ignore",
        case_sensitive=False,
    )

    @property
    def SYNC_DATABASE_URL(self) -> str:

        return f"postgresql+psycopg2://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"

    @property
    def ASYNC_DATABASE_URL(self) -> str:

        return f"postgresql+asyncpg://{self.USER}:{self.PASSWORD}@{self.HOST}:{self.PORT}/{self.NAME}"
