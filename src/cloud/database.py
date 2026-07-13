"""Database setup (SQLAlchemy 2.0 async) — v2.0 Cloud.

Estrutura multi-tenant: cada row de negócio tem `tenant_id`.
Cada request HTTP passa o `tenant_id` automaticamente via JWT.
"""

from collections.abc import AsyncIterator
from contextlib import asynccontextmanager

from sqlalchemy.ext.asyncio import (
    AsyncEngine,
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase

from cloud.config import settings


class Base(DeclarativeBase):
    """Base declarativa pra todos os models. Tenant-safe."""

    pass


# ============================================================
# Engine + session
# ============================================================

engine: AsyncEngine = create_async_engine(
    settings.database_url_async,
    echo=settings.db_echo,
    pool_size=10,
    max_overflow=20,
    pool_pre_ping=True,  # detecta conexão morta
)

async_session_maker = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


async def get_session() -> AsyncIterator[AsyncSession]:
    """Dependency: yields uma AsyncSession por request."""
    async with async_session_maker() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def session_scope() -> AsyncIterator[AsyncSession]:
    """Context manager pra código fora de FastAPI (scripts, jobs)."""
    async with async_session_maker() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


async def init_db() -> None:
    """Cria todas as tabelas. Em produção, use Alembic."""
    from cloud.models import audit, produto, fornecedor, historico, tenant, user  # noqa

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)


async def dispose_db() -> None:
    """Fecha o engine (chamado no shutdown)."""
    await engine.dispose()
