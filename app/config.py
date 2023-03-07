import os
from enum import Enum
from typing import Any

from pydantic import BaseSettings, PostgresDsn, validator


class AppEnvTypes(Enum):
    PROD: str = "prod"
    DEV: str = "dev"
    TEST: str = "test"


class Settings(BaseSettings):
    app_env: AppEnvTypes | None = os.getenv("APP_ENV", default=None)  # type: ignore

    sentry_dsn: str | None = os.getenv("SENTRY_DSN", default=None)

    server_host: str = "0.0.0.0"
    frontend_host: str = "covirally.com"

    secret_jwt_token: str = os.getenv("SECRET_JWT_TOKEN", "")

    database_url: str | PostgresDsn
    max_connection_count: int = 10
    min_connection_count: int = 10

    mailgun_api_key: str | None = os.getenv("MAILGUN_API_KEY")

    @validator("app_env")
    def set_to_default(  # pylint: disable=no-self-argument
        cls, value: AppEnvTypes | None
    ) -> AppEnvTypes:
        if value is None:
            value = AppEnvTypes.PROD
        return value

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
if settings.app_env == AppEnvTypes.PROD:
    assert settings.server_host != "0.0.0.0", "Please provide server host name in .env"
