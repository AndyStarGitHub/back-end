# migrations/env.py
import os
from logging.config import fileConfig

from sqlalchemy import engine_from_config, pool
from alembic import context

from app.core.config import settings  # твій pydantic Settings

# Alembic Config object
config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

# ВАЖЛИВО: sync URL! постарайся мати в Settings вже готовий:
# settings.db.SYNC_DATABASE_URL -> "postgresql+psycopg2://user:pass@db:5432/appdb"
config.set_main_option("sqlalchemy.url", settings.db.SYNC_DATABASE_URL)

target_metadata = None  # або імпортуй Base.metadata, якщо хочеш autogenerate

def run_migrations_offline():
    url = config.get_main_option("sqlalchemy.url")
    context.configure(url=url, compare_type=True, target_metadata=target_metadata)
    with context.begin_transaction():
        context.run_migrations()

def run_migrations_online():
    connectable = engine_from_config(
        config.get_section(config.config_ini_section) or {},
        prefix="sqlalchemy.",
        poolclass=pool.NullPool,
    )
    with connectable.connect() as connection:
        context.configure(connection=connection, compare_type=True, target_metadata=target_metadata)
        with context.begin_transaction():
            context.run_migrations()

if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
