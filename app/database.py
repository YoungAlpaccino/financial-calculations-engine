"""
SQLAlchemy engine + session factory (sketch).
"""
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import get_settings

settings = get_settings()
engine = create_engine(
    settings.db_url, pool_pre_ping=True, pool_size=15, max_overflow=30,
)
SessionFactory = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()


def init_db():
    from app.models import LedgerEvent, RunningTotal, DriftReport   # noqa: F401
    Base.metadata.create_all(bind=engine)


def get_db():
    s = SessionFactory()
    try:
        yield s
    finally:
        s.close()
