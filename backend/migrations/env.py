import asyncio
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine

from app.core.config import settings
from app.core.database import Base


config = context.config

if config.config_file_name is not None:
    fileConfig(config.config_file_name)

target_metadata = Base.metadata


def normalize_async_database_url(url: str) -> str:
    """
    Normalize PostgreSQL URLs for SQLAlchemy async engine.

    Railway/Postgres usually provides:
        postgresql://...

    SQLAlchemy create_async_engine requires an async driver URL:
        postgresql+asyncpg://...

    If this is not normalized, SQLAlchemy falls back to psycopg2 and fails with:
        ModuleNotFoundError: No module named 'psycopg2'
    """

    if not url:
        raise ValueError("DATABASE_URL is missing or empty")

    url = str(url)

    if url.startswith("postgresql+asyncpg://"):
        return url

    if url.startswith("postgresql://"):
        return url.replace("postgresql://", "postgresql+asyncpg://", 1)

    if url.startswith("postgres://"):
        return url.replace("postgres://", "postgresql+asyncpg://", 1)

    return url


def run_migrations_offline() -> None:
    url = normalize_async_database_url(settings.database_url)

    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
        compare_type=True,
    )

    with context.begin_transaction():
        context.run_migrations()


async def run_migrations_online() -> None:
    url = normalize_async_database_url(settings.database_url)

    connectable = create_async_engine(
        url,
        poolclass=pool.NullPool,
    )

    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)

    await connectable.dispose()


if context.is_offline_mode():
    run_migrations_offline()
else:
    asyncio.run(run_migrations_online())