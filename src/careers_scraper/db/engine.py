"""Database engine configuration."""

from sqlalchemy import create_engine
from careers_scraper.config import settings


def get_engine():
    """Create and configure database engine based on settings."""
    return create_engine(
        settings.database_url,
        **settings.engine_kwargs
    )


# Global engine instance
engine = get_engine()
