import logging
import os
import time
from typing import Any, AsyncGenerator

from sqlalchemy import text
from sqlalchemy.ext.asyncio import (
    AsyncSession,
    async_sessionmaker,
    create_async_engine,
)
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.pool import AsyncAdaptedQueuePool, NullPool

from config import settings

logger = logging.getLogger(__name__)

# En modo testing o si se solicita explícitamente, se usa NullPool para aislar conexiones por loop
is_testing = os.getenv("TESTING", "").lower() in ("1", "true", "yes")
pool_class = NullPool if is_testing else AsyncAdaptedQueuePool

# Configuración del motor asíncrono SQLAlchemy para PostgreSQL
# Inyecta automáticamente 'search_path = turismo, public' en cada conexión asyncpg
engine_kwargs: dict[str, Any] = {
    "echo": settings.DEBUG,
    "poolclass": pool_class,
    "connect_args": {
        "server_settings": {
            "search_path": f"{settings.DB_SCHEMA},public"
        }
    },
}

if not is_testing:
    engine_kwargs.update({
        "pool_size": settings.DB_POOL_SIZE,
        "max_overflow": settings.DB_MAX_OVERFLOW,
        "pool_pre_ping": settings.DB_POOL_PRE_PING,
    })

async_engine = create_async_engine(
    settings.DATABASE_URL,
    **engine_kwargs,
)

# Fábrica de sesiones asíncronas
AsyncSessionLocal = async_sessionmaker(
    bind=async_engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False,
)


class Base(DeclarativeBase):
    """Clase base declarativa para los modelos ORM de SQLAlchemy."""
    pass


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Inyector de dependencias FastAPI para obtener una sesión asíncrona de base de datos.
    Garantiza el cierre seguro y control transaccional por petición HTTP.
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()


async def check_db_connectivity() -> dict[str, Any]:
    """
    Verifica la conectividad y latencia con PostgreSQL para el endpoint /health.
    """
    t0 = time.perf_counter()
    try:
        async with AsyncSessionLocal() as session:
            result = await session.execute(text("SELECT version(), count(*) FROM turismo.atractivo"))
            row = result.fetchone()
            latency_ms = round((time.perf_counter() - t0) * 1000, 2)
            db_version = row[0] if row else "Desconocido"
            total_atractivos = row[1] if row else 0

            return {
                "connected": True,
                "latency_ms": latency_ms,
                "version": db_version.split(",")[0] if db_version else "PostgreSQL",
                "total_atractivos": total_atractivos,
                "schema": settings.DB_SCHEMA,
            }
    except Exception as exc:
        latency_ms = round((time.perf_counter() - t0) * 1000, 2)
        logger.error("Error al comprobar conectividad con PostgreSQL: %s", exc)
        return {
            "connected": False,
            "latency_ms": latency_ms,
            "error": str(exc),
            "schema": settings.DB_SCHEMA,
        }
