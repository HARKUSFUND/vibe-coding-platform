"""Database session and engine creation utilities."""

from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker, Session
from loguru import logger

from ...config.settings import Settings


def create_engine_and_session(settings: Settings):
    """
    Create SQLAlchemy engine and session factory.
    Returns (engine, SessionLocal).
    """
    engine = create_engine(
        settings.database_url,
        pool_pre_ping=True,
        pool_size=10,
        max_overflow=20,
        echo=settings.environment == "development",
    )

    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

    return engine, SessionLocal


def test_connection(engine) -> bool:
    """Test database connection."""
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False


def get_session(session_factory) -> Session:
    """Get a new database session."""
    return session_factory()
