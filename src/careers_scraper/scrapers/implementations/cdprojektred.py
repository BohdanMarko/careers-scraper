"""Scraper for CD Projekt Red careers page."""

import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from typing import List, Dict
import time
from careers_scraper.scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class CDProjektRedScraper(BaseScraper):
    """Scraper for CD Projekt Red careers page."""

    def __init__(self, url: str = "https://www.cdprojektred.com/en/jobs"):
        super().__init__("CD Projekt Red", url)

    def scrape(self) -> List[Dict]:
        """Scrape job listings from CD Projekt Red careers page."""
        jobs = []

        # Set up headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)

            driver.get(self.url)

            # Wait for page to load and JavaScript to execute
            time.sleep(5)

            # Extract job data from JavaScript variable
            try:
                jobs_data = driver.execute_script("return window.cdpData.jobsData;")

                if jobs_data and isinstance(jobs_data, list):
                    for job_item in jobs_data:
                        try:
                            # Build detail URL from id + slug (cdprojektred.com/en/jobs/{id}-{slug})
                            job_id = job_item.get('id', '')
                            job_slug = job_item.get('slug', '')
                            apply_url = f"https://www.cdprojektred.com/en/jobs/{job_id}-{job_slug}" if job_id and job_slug else job_item.get('applyUrl', '')

                            # Extract location - handle string, list, or dict
                            location = job_item.get('location', '')
                            if isinstance(location, dict):
                                location = location.get('name', '')
                            elif isinstance(location, list):
                                location = ', '.join(
                                    item.get('name', str(item)) if isinstance(item, dict) else str(item)
                                    for item in location
                                )

                            # Extract category/department - handle dict
                            category = job_item.get('category', '')
                            if isinstance(category, dict):
                                category = category.get('name', '')

                            job = {
                                'title': job_item.get('name', ''),
                                'location': location,
                                'department': category,
                                'url': apply_url,
                                'description': f"Project: {job_item.get('project', 'N/A')} | Remote: {job_item.get('remote', False)}",
                                'posted_date': None
                            }

                            if job['title']:  # Only add if we found a title
                                jobs.append(job)
                        except Exception as e:
                            logger.warning(f"Error parsing job item: {e}")
                            continue
                else:
                    logger.warning("No job data found in window.cdpData.jobsData")

            except Exception as e:
                logger.error(f"Error extracting job data from JavaScript: {e}")

        except Exception as e:
            logger.error(f"Error scraping CD Projekt Red careers page: {e}")
        finally:
            if driver:
                driver.quit()

        logger.info(f"Scraped {len(jobs)} jobs from CD Projekt Red")
        return jobs
