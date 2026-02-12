"""Integration tests for web API endpoints."""

import pytest
from datetime import datetime
from careers_scraper.db.models import Job, CompanyCareerPage


def test_home_page_returns_html(client):
    """Test that home page returns HTML."""
    response = client.get("/")

    assert response.status_code == 200
    assert "text/html" in response.headers["content-type"]


def test_get_jobs_empty(client):
    """Test GET /api/jobs returns empty list when no jobs."""
    response = client.get("/api/jobs")

    assert response.status_code == 200
    assert response.json() == []


def test_get_jobs_with_data(client, test_db):
    """Test GET /api/jobs returns jobs when present."""
    # Create test jobs
    job1 = Job(
        company="Company A",
        title="Python Developer",
        url="https://example.com/job/1",
        location="Remote",
        matches_keywords=True
    )
    job2 = Job(
        company="Company B",
        title="Java Developer",
        url="https://example.com/job/2",
        location="NYC",
        matches_keywords=False
    )
    test_db.add_all([job1, job2])
    test_db.commit()

    response = client.get("/api/jobs")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 2
    assert jobs[0]["company"] in ["Company A", "Company B"]


def test_get_jobs_matching_only(client, test_db):
    """Test GET /api/jobs?matching_only=true filters correctly."""
    # Create test jobs
    matching_job = Job(
        company="Company A",
        title="Python Developer",
        url="https://example.com/job/1",
        matches_keywords=True
    )
    non_matching_job = Job(
        company="Company B",
        title="Sales Manager",
        url="https://example.com/job/2",
        matches_keywords=False
    )
    test_db.add_all([matching_job, non_matching_job])
    test_db.commit()

    response = client.get("/api/jobs?matching_only=true")

    assert response.status_code == 200
    jobs = response.json()
    assert len(jobs) == 1
    assert jobs[0]["title"] == "Python Developer"
    assert jobs[0]["matches_keywords"] is True


def test_get_companies(client, test_db):
    """Test GET /api/companies returns companies."""
    # Create test companies
    company = CompanyCareerPage(
        company_name="Tech Corp",
        url="https://techcorp.com/careers",
        scraper_type="dynamic",
        is_active=True
    )
    test_db.add(company)
    test_db.commit()

    response = client.get("/api/companies")

    assert response.status_code == 200
    companies = response.json()
    assert len(companies) == 1
    assert companies[0]["company_name"] == "Tech Corp"


def test_get_stats(client, test_db):
    """Test GET /api/stats returns correct statistics."""
    # Create test data
    job1 = Job(
        company="Company A",
        title="Python Developer",
        url="https://example.com/job/1",
        matches_keywords=True
    )
    job2 = Job(
        company="Company B",
        title="Sales Manager",
        url="https://example.com/job/2",
        matches_keywords=False
    )
    company = CompanyCareerPage(
        company_name="Test Company",
        url="https://test.com/careers",
        scraper_type="dynamic",
        is_active=True
    )
    test_db.add_all([job1, job2, company])
    test_db.commit()

    response = client.get("/api/stats")

    assert response.status_code == 200
    stats = response.json()
    assert stats["total_jobs"] == 2
    assert stats["matching_jobs"] == 1
    assert stats["total_companies"] == 1
