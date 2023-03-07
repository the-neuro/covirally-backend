import pathlib
import sys
from logging.config import fileConfig

from alembic import context
from sqlalchemy import engine_from_config, pool

from app.config import settings
from app.db.base import Base, database

from app.db.models.users.schemas import User
from app.db.models.tasks.schemas import Task


# curr_path = pathlib.Path(__file__).resolve()
# sys.path.append(str(curr_path.parents[3]))

config = context.config

fileConfig(config.config_file_name)

target_metadata = Base.metadata

config.set_main_option("sqlalchemy.url", str(database.url))


def run_migrations_online() -> None:
    connectable = engine_from_config(
        config.get_section(config.config_ini_section),
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        context.configure(
            connection=connection,
            target_metadata=target_metadata,
            render_as_batch=settings.render_as_batch,
            compare_type=True,
        )

        with context.begin_transaction():
            context.run_migrations()


run_migrations_online()
