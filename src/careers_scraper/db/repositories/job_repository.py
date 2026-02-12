"""Repository for Job model database operations."""

import logging
from typing import List, Optional
from sqlalchemy.orm import Session
from careers_scraper.db.models import Job
from careers_scraper.config import settings

logger = logging.getLogger(__name__)


class JobRepository:
    """Repository class for Job model CRUD operations."""

    def __init__(self, db: Session):
        """
        Initialize repository with database session.

        Args:
            db: SQLAlchemy database session
        """
        self.db = db

    def get_by_url(self, url: str) -> Optional[Job]:
        """
        Get job by URL.

        Args:
            url: Job posting URL

        Returns:
            Job instance or None if not found
        """
        job = self.db.query(Job).filter(Job.url == url).first()
        if job:
            logger.debug(f"Found job by URL: {url}")
        return job

    def get_all(self, offset: int = 0, limit: int = 100) -> List[Job]:
        """
        Get all jobs with pagination.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Job instances
        """
        jobs = (
            self.db.query(Job)
            .order_by(Job.scraped_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        logger.debug(f"Retrieved {len(jobs)} jobs (offset={offset}, limit={limit})")
        return jobs

    def get_matching_keywords(self, offset: int = 0, limit: int = 100) -> List[Job]:
        """
        Get jobs that match search keywords.

        Args:
            offset: Number of records to skip
            limit: Maximum number of records to return

        Returns:
            List of Job instances matching keywords
        """
        jobs = (
            self.db.query(Job)
            .filter(Job.matches_keywords == True)
            .order_by(Job.scraped_at.desc())
            .offset(offset)
            .limit(limit)
            .all()
        )
        logger.debug(
            f"Retrieved {len(jobs)} matching jobs (offset={offset}, limit={limit})"
        )
        return jobs

    def create(self, job: Job) -> Job:
        """
        Create a new job record.

        Args:
            job: Job instance to create

        Returns:
            Created Job instance with ID
        """
        self.db.add(job)
        self.db.commit()
        self.db.refresh(job)
        logger.info(f"Created job: {job.company} - {job.title}")
        return job

    def update(self, job: Job) -> Job:
        """
        Update an existing job record.

        Args:
            job: Job instance to update

        Returns:
            Updated Job instance
        """
        self.db.commit()
        self.db.refresh(job)
        logger.info(f"Updated job: {job.company} - {job.title}")
        return job

    def count(self) -> int:
        """
        Get total count of all jobs.

        Returns:
            Total number of jobs in database
        """
        count = self.db.query(Job).count()
        logger.debug(f"Total jobs count: {count}")
        return count

    def count_matching(self) -> int:
        """
        Get count of jobs matching keywords.

        Returns:
            Number of jobs matching search keywords
        """
        count = self.db.query(Job).filter(Job.matches_keywords == True).count()
        logger.debug(f"Matching jobs count: {count}")
        return count
