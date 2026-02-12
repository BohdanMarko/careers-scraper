"""Repository for CompanyCareerPage model database operations."""

import logging
from typing import List, Optional
from datetime import datetime
from sqlalchemy.orm import Session
from careers_scraper.db.models import CompanyCareerPage

logger = logging.getLogger(__name__)


class CompanyRepository:
    """Repository class for CompanyCareerPage model CRUD operations."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_active(self) -> List[CompanyCareerPage]:
        """
        Get all active company career pages.

        Returns:
            List of active CompanyCareerPage instances
        """
        companies = (
            self.db.query(CompanyCareerPage)
            .filter(CompanyCareerPage.is_active == True)
            .all()
        )
        logger.debug(f"Retrieved {len(companies)} active companies")
        return companies

    def get_all(self) -> List[CompanyCareerPage]:
        """
        Get all company career pages (active and inactive).

        Returns:
            List of all CompanyCareerPage instances
        """
        companies = self.db.query(CompanyCareerPage).all()
        logger.debug(f"Retrieved {len(companies)} total companies")
        return companies

    def get_by_name(self, company_name: str) -> Optional[CompanyCareerPage]:
        """
        Get company by name.

        Args:
            company_name: Company name to search for

        Returns:
            CompanyCareerPage instance or None if not found
        """
        company = (
            self.db.query(CompanyCareerPage)
            .filter(CompanyCareerPage.company_name == company_name)
            .first()
        )
        if company:
            logger.debug(f"Found company: {company_name}")
        return company

    def create(self, company: CompanyCareerPage) -> CompanyCareerPage:
        """
        Create a new company career page record.

        Args:
            company: CompanyCareerPage instance to create

        Returns:
            Created CompanyCareerPage instance with ID
        """
        self.db.add(company)
        self.db.commit()
        self.db.refresh(company)
        logger.info(f"Created company: {company.company_name}")
        return company

    def update_last_scraped(
        self, company: CompanyCareerPage
    ) -> CompanyCareerPage:
        """
        Update the last_scraped timestamp for a company.

        Args:
            company: CompanyCareerPage instance to update

        Returns:
            Updated CompanyCareerPage instance
        """
        company.last_scraped = datetime.utcnow()
        self.db.commit()
        self.db.refresh(company)
        logger.debug(f"Updated last_scraped for: {company.company_name}")
        return company

    def count(self) -> int:
        """
        Get total count of all companies.

        Returns:
            Total number of companies in database
        """
        count = self.db.query(CompanyCareerPage).count()
        logger.debug(f"Total companies count: {count}")
        return count
