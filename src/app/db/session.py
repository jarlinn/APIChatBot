"""
Asynchronous database session management
"""
import logging
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from .database import engine

logger = logging.getLogger(__name__)

AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=True,
    autocommit=False,
)


async def get_async_session() -> AsyncGenerator[AsyncSession, None]:
    """
    FastAPI dependency to get asynchronous database session
    
    Usage:
    @app.get("/items/")
    async def get_items(session: AsyncSession = Depends(get_async_session)):
        # use session here
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
    Context manager to get a database session
    Useful for use outside FastAPI routes
        
    Usage:
    async with get_session() as session:
        # use session here
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
    Manager for more complex database operations
    """
    
    @staticmethod
    async def execute_with_retry(
        operation, 
        max_retries: int = 3,
        session: AsyncSession = None
    ):
        """
        Executes a database operation with automatic retries
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
                import asyncio
                await asyncio.sleep(0.1 * (2 ** attempt))
    
    @staticmethod
    async def health_check() -> bool:
        """
        Verify the health of the database connection.
        """
        try:
            async with get_session() as session:
                await session.execute("SELECT 1")
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False
