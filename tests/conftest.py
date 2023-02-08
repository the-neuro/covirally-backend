import asyncio
from typing import AsyncGenerator
import pytest

from alembic.config import Config
from httpx import AsyncClient

from app.config import settings, AppEnvTypes
from app.db.base import database
from app.db.events import connect_to_db, close_db_connection
from main import app


def pytest_configure(config: Config) -> None:
    """
    Allows plugins and conftest files to perform initial configuration.
    This hook is called for every plugin and initial conftest
    file after command line options have been parsed.
    """
    err = "Can't run tests on non-test environment. Check your APP_ENV variable."
    assert settings.app_env == AppEnvTypes.TEST, err


@pytest.fixture(scope="session")
def event_loop():
    return asyncio.get_event_loop()


@pytest.fixture(scope="session")
def db_url() -> str:
    return str(database.url)


@pytest.fixture(autouse=True, scope="module")
async def connect_db(db_url: str) -> AsyncGenerator:
    try:
        await connect_to_db()
        yield
    finally:
        await close_db_connection()


@pytest.fixture(scope="session")
async def async_client() -> AsyncClient:
    """
    Async httpx client to test API
    """
    a_client = AsyncClient(app=app, base_url="http://test")
    try:
        yield a_client
    finally:
        await a_client.aclose()
