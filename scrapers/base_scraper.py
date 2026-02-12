from abc import ABC, abstractmethod
from typing import List, Dict
from datetime import datetime


class BaseScraper(ABC):
    """Base class for all career page scrapers"""

    def __init__(self, company_name: str, url: str):
        self.company_name = company_name
        self.url = url

    @abstractmethod
    def scrape(self) -> List[Dict]:
        """
        Scrape job listings from the career page

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
        """Check if job matches any of the keywords"""
        searchable_text = " ".join([
            job.get('title', ''),
            job.get('description', ''),
            job.get('department', '')
        ]).lower()

        return any(keyword.lower() in searchable_text for keyword in keywords)
