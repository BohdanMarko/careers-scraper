"""Unit tests for configuration module."""

import pytest
from careers_scraper.config import Settings


def test_settings_defaults():
    """Test that default settings are loaded correctly."""
    settings = Settings()
    assert settings.environment == "development"
    assert settings.debug is False
    assert "sqlite" in settings.database_url
    assert settings.web_host == "0.0.0.0"
    assert settings.web_port == 8000


def test_keywords_list_property():
    """Test that keywords_list property splits and lowercases keywords."""
    settings = Settings(search_keywords="Python,Backend,Developer")
    keywords = settings.keywords_list

    assert len(keywords) == 3
    assert "python" in keywords
    assert "backend" in keywords
    assert "developer" in keywords


def test_keywords_list_with_spaces():
    """Test that keywords_list handles spaces correctly."""
    settings = Settings(search_keywords=" Python , Backend , Developer ")
    keywords = settings.keywords_list

    assert len(keywords) == 3
    assert "python" in keywords
    assert "backend" in keywords
    assert "developer" in keywords


def test_engine_kwargs_sqlite():
    """Test engine_kwargs for SQLite database."""
    settings = Settings(database_url="sqlite:///./test.db")
    kwargs = settings.engine_kwargs

    assert "connect_args" in kwargs
    assert kwargs["connect_args"]["check_same_thread"] is False


def test_engine_kwargs_postgresql():
    """Test engine_kwargs for PostgreSQL database."""
    settings = Settings(database_url="postgresql://user:pass@localhost/dbname")
    kwargs = settings.engine_kwargs

    assert "pool_size" in kwargs
    assert kwargs["pool_size"] == 5
    assert "max_overflow" in kwargs
    assert kwargs["max_overflow"] == 10
    assert "pool_pre_ping" in kwargs
    assert kwargs["pool_pre_ping"] is True
    assert "pool_recycle" in kwargs
    assert kwargs["pool_recycle"] == 3600


def test_settings_with_env_prefix():
    """Test that CAREERS_ prefix is configured."""
    import os
    os.environ["CAREERS_WEB_PORT"] = "9000"

    settings = Settings()
    assert settings.web_port == 9000

    # Cleanup
    del os.environ["CAREERS_WEB_PORT"]


def test_scrape_interval_default():
    """Test default scrape interval."""
    settings = Settings()
    assert settings.scrape_interval == 60
