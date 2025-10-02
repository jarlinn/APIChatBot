"""Init DB module"""

import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.app.db.database import Base
from src.app.config import settings
import logging

logger = logging.getLogger(__name__)


async def init_db():
    """Initializes the database"""
    try:
        database_url = settings.postgresql_url
        logger.info(f"Initializing database: {database_url}")

        engine = create_async_engine(
            database_url,
            echo=settings.database_echo,
        )

        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        logger.info("Database tables successfully created")

        await engine.dispose()

    except Exception as e:
        print(f"💥 Error al inicializar la base de datos: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(init_db())
