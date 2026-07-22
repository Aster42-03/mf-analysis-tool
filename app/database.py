from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase

DB_URL = "postgresql+:asyncpg//aster:aster42@localhost:5432/mf_analytics"

engine = create_async_engine(DB_URL, pool_size=5, max_overflow=15, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


AsyncSessionLocal = async_sessionmaker(bind=engine, autoflush=False)
