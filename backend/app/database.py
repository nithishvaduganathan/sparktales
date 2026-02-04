"""
Database configuration and session management for AWS RDS
"""
from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker
from app.config import get_settings

settings = get_settings()

# Use the database URL directly (supports postgresql:// format)
database_url = settings.database_url

# Create SQLAlchemy engine for RDS PostgreSQL
engine = create_engine(
    database_url,
    pool_pre_ping=True,  # Verify connection before use
    pool_size=10,
    max_overflow=20,
    pool_recycle=3600,  # Recycle connections after 1 hour
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()


def get_db():
    """Dependency to get database session"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def init_db():
    """Initialize database tables"""
    from app import models  # noqa: F401
    Base.metadata.create_all(bind=engine)
