from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

DB_URL = "postgresql+psycopg://mf_worker:worker123@localhost:5432/mf_data"

engine = create_engine(DB_URL, pool_size=5, max_overflow=15, pool_pre_ping=True)
