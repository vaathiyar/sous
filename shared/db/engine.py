from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import shared.config  # noqa: F401 — ensures settings are loaded
from shared.config import settings
from shared.db.models import Base

_engine = None
_SessionLocal = None


def get_engine():
    global _engine
    if _engine is None:
        if not settings.sql_database_url:
            raise RuntimeError("SQL_DATABASE_URL is not set in .env")
        _engine = create_engine(settings.sql_database_url)
    return _engine


def get_session():
    global _SessionLocal
    if _SessionLocal is None:
        _SessionLocal = sessionmaker(bind=get_engine())
    return _SessionLocal()


def create_tables():
    Base.metadata.create_all(get_engine())
