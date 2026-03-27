"""
Async SQLAlchemy engine and session factory.
Import `AsyncSessionLocal` wherever a database session is needed (via the get_db dependency).
"""

from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker

from app.core.config import settings

# echo=False in production — set to True locally if you want to see SQL queries
engine = create_async_engine(settings.DATABASE_URL, echo=False, future=True)

AsyncSessionLocal = sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,  # Keeps ORM objects usable after commit without re-querying
)
