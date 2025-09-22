"""
Gestión de sesiones de base de datos asíncronas
Compatible con PostgreSQL y SQLite
"""
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager
from typing import AsyncGenerator
import logging

from .database import engine

logger = logging.getLogger(__name__)

# Create AsyncSessionLocal class con configuración optimizada
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


# Dependency para FastAPI - Inyección de dependencias
async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependencia de FastAPI para obtener una sesión de base de datos asíncrona
    
    Usage:
        @app.get("/items/")
        async def get_items(session: AsyncSession = Depends(get_async_session)):
            # usar session aquí
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


@asynccontextmanager
async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """
    Context manager para obtener una sesión de base de datos
    Útil para uso fuera de FastAPI routes
    
    Usage:
        async with get_session() as session:
            # usar session aquí
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
        except SQLAlchemyError as e:
            logger.error(f"Database session error: {e}")
            await session.rollback()
            raise
        finally:
            await session.close()


class DatabaseManager:
    """
    Manager para operaciones de base de datos más complejas
    """
    
    @staticmethod
    async def execute_with_retry(
        operation, 
        max_retries: int = 3,
        session: AsyncSession = None
    ):
        """
        Ejecuta una operación de base de datos con reintentos automáticos
        """
        for attempt in range(max_retries):
            try:
                if session:
                    return await operation(session)
                else:
                    async with get_session() as session:
                        return await operation(session)
            except SQLAlchemyError as e:
                logger.warning(f"Database operation failed (attempt {attempt + 1}): {e}")
                if attempt == max_retries - 1:
                    raise
                # Esperar un poco antes del siguiente intento
                import asyncio
                await asyncio.sleep(0.1 * (2 ** attempt))
    
    @staticmethod
    async def health_check() -> bool:
        """
        Verifica la salud de la conexión a la base de datos
        """
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
