from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


def verify_conn(url):
    if not url:
        raise ValueError(
            "CRITICAL ERROR: DB_URL environment variable is missing or None!"
        )
    return url


link = verify_conn(settings.db_url)
print(f"Connecting to DataBase at: {link}")

engine = create_async_engine(link, pool_size=5, max_overflow=15, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


AsyncSessionLocal = async_sessionmaker(engine, autoflush=False)
