"""Pytest configuration and shared fixtures."""

import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from datetime import datetime
from fastapi.testclient import TestClient

from careers_scraper.db.models import Base, Job, CompanyCareerPage
from careers_scraper.web import app


@pytest.fixture(scope="function")
def test_db():
    """Create an in-memory SQLite database for testing."""
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)

    TestSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = TestSessionLocal()

    try:
        yield db
    finally:
        db.close()
        Base.metadata.drop_all(engine)


@pytest.fixture
def sample_job(test_db):
    """Create a sample job for testing."""
    job = Job(
        company="Test Company",
        title="Senior Python Developer",
        location="Remote",
        department="Engineering",
        url="https://example.com/job/123",
        description="Great Python job",
        posted_date=datetime(2024, 1, 1),
        matches_keywords=True,
        notified=False
    )
    test_db.add(job)
    test_db.commit()
    test_db.refresh(job)
    return job


@pytest.fixture
def sample_company(test_db):
    """Create a sample company for testing."""
    company = CompanyCareerPage(
        company_name="Test Company",
        url="https://example.com/careers",
        scraper_type="dynamic",
        is_active=True,
        last_scraped=None
    )
    test_db.add(company)
    test_db.commit()
    test_db.refresh(company)
    return company


@pytest.fixture
def client(test_db):
    """Create a test client with database override."""
    from careers_scraper.db import get_db

    def override_get_db():
        try:
            yield test_db
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db

    with TestClient(app) as test_client:
        yield test_client

    app.dependency_overrides.clear()
