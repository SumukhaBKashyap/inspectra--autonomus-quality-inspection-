"""Database utilities for Inspectra.
Uses SQLite via SQLAlchemy.
"""

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

SQLITE_DB_PATH = "inspectra.db"
engine = create_engine(f"sqlite:///{SQLITE_DB_PATH}", connect_args={"check_same_thread": False})
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def init_db():
    """Create tables if they do not exist."""
    from . import models  # noqa: F401 – ensures models are registered
    Base.metadata.create_all(bind=engine)
