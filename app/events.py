from collections.abc import Callable

from app.db.events import close_db_connection, connect_to_db
from app.http_cli.events import close_http_cli


def create_start_app_handler() -> Callable:  # type: ignore
    async def start_app() -> None:
        await connect_to_db()

    return start_app


def create_stop_app_handler() -> Callable:  # type: ignore
    async def close_app() -> None:
        await close_db_connection()
        await close_http_cli()

    return close_app
