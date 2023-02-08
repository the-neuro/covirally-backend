import os
from argparse import Namespace
from pathlib import Path
from types import SimpleNamespace

from alembic.config import Config

PROJECT_PATH = Path(__file__).parent.parent.resolve()


def _make_alembic_config(
    cmd_opts: Namespace | SimpleNamespace, base_path: str = PROJECT_PATH
) -> Config:
    """
    Creates alembic config based on args
    """
    if not os.path.isabs(cmd_opts.config):
        cmd_opts.config = os.path.join(base_path, cmd_opts.config)

    config = Config(file_=cmd_opts.config, ini_section=cmd_opts.name, cmd_opts=cmd_opts)

    alembic_location = config.get_main_option("script_location")
    if not os.path.isabs(alembic_location):
        config.set_main_option(
            "script_location", os.path.join(base_path, alembic_location)
        )
    if cmd_opts.pg_url:
        config.set_main_option("sqlalchemy.url", cmd_opts.pg_url)

    return config


def get_alembic_config(db_url: str) -> Config:
    """
    Creates object with alembic config, which is set up on temproray DB
    """
    cmd_options = SimpleNamespace(
        config="alembic.ini", name="alembic", pg_url=db_url, raiseerr=False, x=None
    )
    return _make_alembic_config(cmd_options)
