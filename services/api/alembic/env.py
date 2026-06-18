import os
import sys
from logging.config import fileConfig

from sqlalchemy import pool, create_engine
from sqlalchemy.engine import Connection

from alembic import context

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))

config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)

from shared.database import Base

import auth.models
import document.models
import audit.models
import ai_forge.models
import approval.models

target_metadata = Base.metadata


def run_migrations_offline() -> None:
    url = config.get_main_option("sqlalchemy.url")
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection: Connection) -> None:
    context.configure(connection=connection, target_metadata=target_metadata)

    with context.begin_transaction():
        context.run_migrations()


def run_migrations_online() -> None:
    connectable = create_engine(
        config.get_main_option("sqlalchemy.url"),
        poolclass=pool.NullPool,
    )

    with connectable.connect() as connection:
        do_run_migrations(connection)

    connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
