"""
Database connection setup for EcoPath AI.
Uses SQLAlchemy for ORM and connection pooling.
"""

import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base
from app.config import settings

logger = logging.getLogger(__name__)

# Create engine with connection pooling
engine = create_engine(
    settings.DATABASE_URL,
    pool_size=5,           # Keep 5 connections open
    max_overflow=10,       # Allow 10 extra connections under load
    pool_pre_ping=True,    # Test connections before using them
    echo=False,            # Set True to see SQL queries in logs
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for all models
Base = declarative_base()


def get_db():
    """
    Dependency that provides a database session.
    Automatically closes session when done.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """
    Create all tables if they don't exist.
    Called once on app startup.
    """
    try:
        from app.db import models  # noqa — must import so SQLAlchemy knows about all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created/verified successfully")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise