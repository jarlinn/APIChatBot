from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.orm import sessionmaker
import os

# Database URL - will be loaded from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chatbot.db")

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

# Create AsyncSessionLocal class
AsyncSessionLocal = sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)

# Dependency to get async DB session
async def get_async_session():
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()
