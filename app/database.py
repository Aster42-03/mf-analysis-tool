from sqlalchemy import create_engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.orm import DeclarativeBase

DB_URL = "postgresql+psycopg://mf_worker:worker123@localhost:5432/mf_analytics"

engine = create_engine(DB_URL, pool_size=5, max_overflow=15, pool_pre_ping=True)


class Base(DeclarativeBase):
    pass


session = sessionmaker(engine, autoflush=False)
