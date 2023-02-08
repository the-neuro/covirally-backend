import databases
import sqlalchemy
from databases import Database
from pydantic import PostgresDsn
from sqlalchemy.ext.declarative import declarative_base
from yarl import URL

from app.config import settings, AppEnvTypes

db_options = settings.db_options

Base = declarative_base()

metadata = sqlalchemy.MetaData()


def get_test_db_url(db_url: str | PostgresDsn, end_sufix: str = "test") -> str:
    """
    Replace name of db with test sufix.
    From this: postgresql://postgres:postgres@0.0.0.0:5432/postgres
    To this: postgresql://postgres:postgres@0.0.0.0:5432/test
    """
    return str(URL(str(db_url)).with_path(end_sufix))


def get_db(db_url: str | PostgresDsn) -> Database:
    force_rollback = False
    if settings.app_env == AppEnvTypes.TEST:
        force_rollback = True
        db_url = get_test_db_url(db_url=db_url)

    return databases.Database(url=db_url, force_rollback=force_rollback, **db_options)


database = get_db(db_url=settings.database_url)
