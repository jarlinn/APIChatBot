"""
Configuración de la base de datos con soporte para PostgreSQL y pgvector
"""
from sqlalchemy.ext.asyncio import create_async_engine, AsyncEngine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.pool import NullPool, StaticPool
from sqlalchemy import event
import logging
from ..config import settings

logger = logging.getLogger(__name__)

# Create Base class
Base = declarative_base()


def create_database_engine() -> AsyncEngine:
    """
    Crea el motor de base de datos con configuración optimizada
    """
    database_url = settings.get_database_url()
    
    # Configuración específica según el tipo de base de datos
    engine_kwargs = {
        "echo": settings.database_echo,
        "future": True,  # Usar SQLAlchemy 2.0 style
    }
    
    if "postgresql" in database_url:
        # Configuración optimizada para PostgreSQL con pool de conexiones
        engine_kwargs.update({
            "pool_size": settings.db_pool_size,
            "max_overflow": settings.db_max_overflow,
            "pool_timeout": settings.db_pool_timeout,
            "pool_recycle": settings.db_pool_recycle,
            "pool_pre_ping": True,  # Verificar conexiones antes de usar
            "pool_reset_on_return": "commit",  # Reset automático de transacciones
        })
        logger.info(f"Configurando PostgreSQL async engine con pool: {settings.db_pool_size}+{settings.db_max_overflow} conexiones")
    else:
        # Configuración para SQLite (desarrollo)
        engine_kwargs.update({
            "poolclass": NullPool,
            "connect_args": {"check_same_thread": False}
        })
        logger.info("Configurando SQLite engine para desarrollo")
    
    engine = create_async_engine(database_url, **engine_kwargs)
    
    # Event listeners para PostgreSQL
    if "postgresql" in database_url:
        @event.listens_for(engine.sync_engine, "connect")
        def set_postgresql_search_path(dbapi_connection, connection_record):
            """Configurar search_path y extensiones necesarias"""
            try:
                cursor = dbapi_connection.cursor()
                # Asegurar que la extensión vector esté disponible
                cursor.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                # Configurar search_path si es necesario
                cursor.execute("SET search_path TO public;")
                dbapi_connection.commit()
                cursor.close()
            except Exception as e:
                logger.warning(f"No se pudo configurar PostgreSQL: {e}")
                # Continuar sin configuración específica
    
    return engine


# Crear instancia global del motor
engine = create_database_engine()


# Dependency to get DB session (for backward compatibility)
def get_db():
    """
    Función de compatibilidad hacia atrás
    Para nuevas implementaciones, usar get_async_session de session.py
    """
    raise NotImplementedError(
        "Use get_async_session from session.py for async operations. "
        "This function is kept for backward compatibility only."
    )
