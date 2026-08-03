"""
Shared pytest fixtures. The `db` fixture builds a fresh in-memory SQLite
database seeded with the real dataset for every test — fast (no disk I/O),
fully isolated between tests, and exercises the exact same seed_data.py
logic used in production, so a bug in seeding shows up here too.
"""

import sys
from pathlib import Path

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# allow `from database.models import ...` etc. when running pytest from backend/
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from database.models import Base  # noqa: E402
import database.seed_data as seed_data  # noqa: E402


@pytest.fixture()
def db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    seed_data.seed(session)
    yield session
    session.close()