"""Base class for all career page scrapers."""

import logging
from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime

logger = logging.getLogger(__name__)


class BaseScraper(ABC):
    """Base class for all career page scrapers."""

    def __init__(self, company_name: str, url: str):
        """
        Initialize scraper with company information.

        Args:
            company_name: Name of the company
            url: Career page URL
        """
        self.company_name = company_name
        self.url = url
        logger.debug(f"Initialized scraper for {company_name}: {url}")

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Scrape job listings from the career page.

        Returns:
            List of dictionaries with job information:
            {
                'title': str,
                'location': str,
                'department': str,
                'url': str,
                'description': str,
                'posted_date': datetime or None
            }
        """
        pass

    def matches_keywords(self, job: Dict, keywords: List[str]) -> bool:
        """
        Check if job matches any of the search keywords.

        Args:
            job: Job dictionary with title, description, department
            keywords: List of keywords to search for

        Returns:
            True if any keyword matches, False otherwise
        """
        searchable_text = " ".join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('department', '')
        ]).lower()

        matches = any(keyword.lower() in searchable_text for keyword in keywords)
        if matches:
            logger.debug(
                f"Job '{job.get('title', 'Unknown')}' matches keywords"
            )
        return matches
