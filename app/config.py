from enum import Enum
from typing import Any

from pydantic import BaseSettings, PostgresDsn


class AppEnvTypes(Enum):
    PROD: str = "prod"
    DEV: str = "dev"
    TEST: str = "test"


class Settings(BaseSettings):
    app_env: AppEnvTypes = AppEnvTypes.PROD

    sentry_dsn: str

    database_url: str | PostgresDsn
    max_connection_count: int = 10
    min_connection_count: int = 10

    @property
    def db_options(self) -> dict[str, Any]:
        if "postgres" in self.database_url:
            options = {
                "min_size": self.min_connection_count,
                "max_size": self.max_connection_count,
            }
        elif "sqlite" in self.database_url:
            options = {}
        else:
            raise ValueError(f"Unknown db engine = {self.database_url}")
        return options

    @property
    def render_as_batch(self) -> bool:
        return "sqlite" in self.database_url

    class Config:
        env_file = ".env"


settings = Settings()