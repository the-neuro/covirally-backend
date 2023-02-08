from uuid import uuid4

import pytest
from alembic.config import Config
from pydantic import PostgresDsn
from sqlalchemy_utils import create_database, drop_database
from yarl import URL

from tests.db_alembic_utils import get_alembic_config


def get_tmp_db_url(db_url: str | PostgresDsn) -> str:
    """
    Replace name of db with random one.
    """
    tmp_name = '.'.join([uuid4().hex, 'pytest'])
    tmp_url = str(URL(db_url).with_path(tmp_name))
    return tmp_url


@pytest.fixture
def tmp_db(db_url: str):
    """
    Creates tmp DB without applied migrations.
    :returns url for this db.
    """
    tmp_url = get_tmp_db_url(db_url=db_url)
    create_database(tmp_url)

    try:
        yield tmp_url
    finally:
        drop_database(tmp_url)


@pytest.fixture()
def alembic_config(tmp_db: str) -> Config:
    config: Config = get_alembic_config(db_url=tmp_db)
    return config
