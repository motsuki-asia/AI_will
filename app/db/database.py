"""Database connection and session management"""
from typing import AsyncGenerator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine

from app.core.config import settings

# Create async engine
# For SQLite, use aiosqlite driver
if settings.DATABASE_URL.startswith("sqlite"):
    # Convert sqlite:// to sqlite+aiosqlite://
    database_url = settings.DATABASE_URL.replace("sqlite://", "sqlite+aiosqlite://")
    engine = create_async_engine(
        database_url,
        echo=settings.DEBUG,
        connect_args={"check_same_thread": False},
    )
else:
    engine = create_async_engine(
        settings.DATABASE_URL,
        echo=settings.DEBUG,
        pool_pre_ping=True,
    )

# Session factory
AsyncSessionLocal = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autocommit=False,
    autoflush=False,
)


async def get_db() -> AsyncGenerator[AsyncSession, None]:
    """
    Dependency that provides a database session.
    
    Usage:
        @router.get("/")
        async def endpoint(db: AsyncSession = Depends(get_db)):
            ...
    """
    async with AsyncSessionLocal() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()
