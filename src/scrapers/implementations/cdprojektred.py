"""Scraper for CD Projekt Red careers page."""

import logging
from typing import List, Dict
from selenium.webdriver.support.ui import WebDriverWait
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CDProjektRedScraper(BaseScraper):
    """Scraper for CD Projekt Red careers page."""

    def __init__(self, url: str = "https://www.cdprojektred.com/en/jobs"):
        super().__init__("CD Projekt Red", url)

    def _attempt_scrape(self, driver) -> List[Dict]:
        """Single scraping attempt — load page, wait for JS data, extract jobs."""
        driver.get(self.url)

        WebDriverWait(driver, 30).until(
            lambda d: d.execute_script(
                "return typeof window.cdpData !== 'undefined'"
                " && window.cdpData !== null"
                " && window.cdpData.jobsData !== null"
            )
        )

        jobs_data = driver.execute_script("return window.cdpData.jobsData;")

        if not jobs_data or not isinstance(jobs_data, list):
            logger.warning("CD Projekt Red: window.cdpData.jobsData is empty or not a list")
            return []

        jobs = []
        for job_item in jobs_data:
            try:
                job_id = job_item.get('id', '')
                job_slug = job_item.get('slug', '')
                apply_url = (
                    f"https://www.cdprojektred.com/en/jobs/{job_id}-{job_slug}"
                    if job_id and job_slug
                    else job_item.get('applyUrl', '')
                )

                location = job_item.get('location', '')
                if isinstance(location, dict):
                    location = location.get('name', '')
                elif isinstance(location, list):
                    location = ', '.join(
                        item.get('name', str(item)) if isinstance(item, dict) else str(item)
                        for item in location
                    )

                category = job_item.get('category', '')
                if isinstance(category, dict):
                    category = category.get('name', '')

                title = job_item.get('name', '')
                if not title:
                    continue

                jobs.append({
                    'title': title,
                    'location': location,
                    'department': category,
                    'url': apply_url,
                    'description': f"Project: {job_item.get('project', 'N/A')} | Remote: {job_item.get('remote', False)}",
                    'posted_date': None,
                })
            except Exception as e:
                logger.warning("CD Projekt Red: error parsing job item: %s", e, exc_info=True)
                continue

        return jobs
