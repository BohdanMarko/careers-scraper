"""Unit tests for database repository classes."""

import pytest
from datetime import datetime
from careers_scraper.db.models import Job, CompanyCareerPage
from careers_scraper.db.repositories import JobRepository, CompanyRepository


class TestJobRepository:
    """Tests for JobRepository class."""

    def test_get_by_url_found(self, test_db, sample_job):
        """Test get_by_url returns job when found."""
        repo = JobRepository(test_db)
        job = repo.get_by_url(sample_job.url)

        assert job is not None
        assert job.id == sample_job.id
        assert job.title == sample_job.title

    def test_get_by_url_not_found(self, test_db):
        """Test get_by_url returns None when not found."""
        repo = JobRepository(test_db)
        job = repo.get_by_url("https://nonexistent.com/job/999")

        assert job is None

    def test_create_job(self, test_db):
        """Test creating a new job."""
        repo = JobRepository(test_db)

        new_job = Job(
            company="New Company",
            title="Backend Engineer",
            url="https://example.com/job/456",
            location="New York",
            department="Engineering",
            matches_keywords=False
        )

        created_job = repo.create(new_job)

        assert created_job.id is not None
        assert created_job.title == "Backend Engineer"
        assert created_job.company == "New Company"

    def test_count(self, test_db, sample_job):
        """Test counting all jobs."""
        repo = JobRepository(test_db)
        count = repo.count()

        assert count == 1

    def test_count_matching(self, test_db, sample_job):
        """Test counting matching jobs."""
        repo = JobRepository(test_db)

        # Create a non-matching job
        non_matching = Job(
            company="Other Company",
            title="Sales Manager",
            url="https://example.com/job/789",
            matches_keywords=False
        )
        test_db.add(non_matching)
        test_db.commit()

        count_matching = repo.count_matching()

        assert count_matching == 1  # Only sample_job matches


class TestCompanyRepository:
    """Tests for CompanyRepository class."""

    def test_get_active(self, test_db, sample_company):
        """Test get_active returns only active companies."""
        repo = CompanyRepository(test_db)

        # Create an inactive company
        inactive_company = CompanyCareerPage(
            company_name="Inactive Company",
            url="https://inactive.com/careers",
            scraper_type="dynamic",
            is_active=False
        )
        test_db.add(inactive_company)
        test_db.commit()

        active_companies = repo.get_active()

        assert len(active_companies) == 1
        assert active_companies[0].company_name == "Test Company"

    def test_create_company(self, test_db):
        """Test creating a new company."""
        repo = CompanyRepository(test_db)

        new_company = CompanyCareerPage(
            company_name="New Tech Corp",
            url="https://newtech.com/careers",
            scraper_type="static",
            is_active=True
        )

        created_company = repo.create(new_company)

        assert created_company.id is not None
        assert created_company.company_name == "New Tech Corp"
        assert created_company.scraper_type == "static"

    def test_get_by_name(self, test_db, sample_company):
        """Test get_by_name finds company."""
        repo = CompanyRepository(test_db)
        company = repo.get_by_name("Test Company")

        assert company is not None
        assert company.id == sample_company.id
