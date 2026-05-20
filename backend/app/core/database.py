from collections.abc import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from app.core.config import settings


def normalize_async_database_url(url: str) -> str:
    """
    Normalize PostgreSQL URLs for SQLAlchemy async engine.

    Railway/Postgres commonly provides:
        postgresql://...
    or sometimes:
        postgres://...

    SQLAlchemy create_async_engine must receive an async driver URL:
        postgresql+asyncpg://...

    Without this normalization, SQLAlchemy tries to use psycopg2,
    which causes:
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


database_url = normalize_async_database_url(settings.database_url)

engine = create_async_engine(
    database_url,
    echo=False,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


class Base(DeclarativeBase):
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    async with async_session_factory() as session:
        yield session
