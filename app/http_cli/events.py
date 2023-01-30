from app.http_cli import http_client


async def close_http_cli() -> None:
    await http_client.aclose()
