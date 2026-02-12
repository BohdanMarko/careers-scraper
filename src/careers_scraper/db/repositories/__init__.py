"""Database repository classes."""

from careers_scraper.db.repositories.job_repository import JobRepository
from careers_scraper.db.repositories.company_repository import CompanyRepository

__all__ = ["JobRepository", "CompanyRepository"]
