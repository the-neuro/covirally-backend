import logging
import os
import sys

from app.config import settings
from app.db.base import database

logging.basicConfig(stream=sys.stdout, level=logging.INFO)
logger = logging.getLogger(__name__)


async def connect_to_db() -> None:
    logger.info("Connecting to Database")

    # todo: uncomment
    print(f'{os.getenv("DATABASE_URL")=}')
    print(f'{settings.database_url=}')
    # await database.connect()

    logger.info("Connection established")


async def close_db_connection() -> None:
    logger.info("Closing connection to database")

    await database.disconnect()

    logger.info("Connection closed")
