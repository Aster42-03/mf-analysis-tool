from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from .config import settings


DB_URL = settings.db_url

if not DB_URL:
    raise ValueError( "CRITICAL ERROR: DB_URL environment variable is missing or None!" )

print( f"Connecting to database at: {DB_URL}" )

engine = create_async_engine( DB_URL, pool_size = 5, max_overflow = 15, pool_pre_ping = True )


class Base( DeclarativeBase ):
    pass


AsyncSessionLocal = async_sessionmaker( engine, autoflush = False )
