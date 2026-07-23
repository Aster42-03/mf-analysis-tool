import os

from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from dotenv import load_dotenv

load_dotenv()

DB_URL = f"postgresql+:asyncpg//{os.getenv("DB_USER")}:{os.getenv("DB_PASSWORD")}@{os.getenv("DB_HOST")}:{os.getenv("DB_PORT")}/{os.getenv("DB_NAME")}"

engine = create_async_engine(DB_URL, pool_size=5, max_overflow=15, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


AsyncSessionLocal = async_sessionmaker(engine, autoflush=False)
