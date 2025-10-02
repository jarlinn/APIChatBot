"""
Database configuration with support for PostgreSQL and pgvector
"""

import logging

from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy import event

from ..config import settings

logger = logging.getLogger(__name__)

Base = declarative_base()

POOL_SIZE = 20
MAX_OVERFLOW = 30
POOL_TIMEOUT = 30
POOL_RECYCLE = 3600


def create_database_engine() -> AsyncEngine:
    """
    Creates the database engine with optimized configuration
    """
    database_url = settings.postgresql_url


    engine_kwargs = {
        "echo": settings.database_echo,
        "future": True,
    }
    
    if "postgresql" not in database_url and "postgresql+asyncpg" not in database_url:
        raise ValueError(
            f"Only PostgreSQL is allowed. Database URL provided: {database_url}"
        )

    engine_kwargs.update({
        "pool_size": POOL_SIZE,
        "max_overflow": MAX_OVERFLOW,
        "pool_timeout": POOL_TIMEOUT,
        "pool_recycle": POOL_RECYCLE,
        "pool_pre_ping": True,
        "pool_reset_on_return": "commit",
    })
    
    logger.info(f"Configuring PostgreSQL async engine with pool: {POOL_SIZE}+{MAX_OVERFLOW} connections")
    
    engine = create_async_engine(database_url, **engine_kwargs)
    
    # Event listeners for PostgreSQL
    @event.listens_for(engine.sync_engine, "connect")
    def set_postgresql_search_path(dbapi_connection, connection_record):
        """Configure search_path and necessary extensions“”‘’“”"""
        try:
            cursor = dbapi_connection.cursor()
            cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
            cursor.execute("SET search_path TO public;")
            dbapi_connection.commit()
            cursor.close()
        except Exception as e:
            logger.error(f"PostgreSQL could not be configured: {e}")
            raise RuntimeError(f"PostgreSQL could not be configured: {e}") from e
    return engine

engine = create_database_engine()
