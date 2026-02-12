"""Database session management."""

from sqlalchemy.orm import sessionmaker
from careers_scraper.db.engine import engine

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """
    Database session generator for dependency injection.

    Yields:
        Session: SQLAlchemy database session

    Example:
        >>> for db in get_db():
        ...     jobs = db.query(Job).all()
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
