from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
import os

# Database URL - will be loaded from environment variables
DATABASE_URL = os.getenv("DATABASE_URL", "sqlite+aiosqlite:///./chatbot.db")

# Create async SQLAlchemy engine
engine = create_async_engine(
    DATABASE_URL,
    echo=True,
)

# Create Base class
Base = declarative_base()

# Dependency to get DB session (for backward compatibility)
def get_db():
    # This is kept for backward compatibility but should not be used
    # Use get_async_session from session.py instead
    raise NotImplementedError("Use get_async_session from session.py for async operations")
