"""
DB engine/session setup used by the FastAPI app (as opposed to seed_data.py,
which manages its own engine for standalone seeding runs).
"""

from sqlalchemy.orm import sessionmaker

from config import settings
from database.models import get_engine, init_db

engine = get_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)


def init() -> None:
    """Create tables if they don't exist yet. Safe to call on every startup."""
    init_db(engine)


def get_db():
    """FastAPI dependency: yields a request-scoped session, closes it after."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()