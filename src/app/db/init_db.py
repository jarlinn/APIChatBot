import asyncio
from sqlalchemy.ext.asyncio import create_async_engine
from src.app.db.database import Base
from src.app.models.user import User

async def init_db():
    # Create async engine
    engine = create_async_engine(
        "sqlite+aiosqlite:///./chatbot.db",
        echo=True,
    )
    
    async with engine.begin() as conn:
        # Create all tables
        await conn.run_sync(Base.metadata.create_all)
    
    print("Database initialized successfully!")
    await engine.dispose()

if __name__ == "__main__":
    asyncio.run(init_db())
