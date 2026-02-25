"""Base class for all career page scrapers."""

import logging
import os
import time
from abc import ABC, abstractmethod
from typing import List, Dict
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service

logger = logging.getLogger(__name__)


def create_chrome_driver() -> webdriver.Chrome:
    """Create a headless Chrome driver. Reads CHROME_BINARY and CHROMEDRIVER_PATH env vars."""
    opts = Options()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    opts.add_argument("--disable-gpu")
    opts.add_argument("--window-size=1920,1080")
    chrome_binary = os.environ.get("CHROME_BINARY")
    if chrome_binary:
        opts.binary_location = chrome_binary
    chromedriver_path = os.environ.get("CHROMEDRIVER_PATH")
    service = Service(executable_path=chromedriver_path) if chromedriver_path else None
    driver = webdriver.Chrome(options=opts, service=service) if service else webdriver.Chrome(options=opts)
    driver.set_page_load_timeout(30)
    driver.implicitly_wait(0)
    return driver


class BaseScraper(ABC):
    """Base class for all career page scrapers.

    Subclasses implement _attempt_scrape(driver) only. This class handles
    driver lifecycle, retry logic, and logging around each attempt.

    Class attributes to override per scraper:
        _MAX_ATTEMPTS: total attempts before giving up (default 2)
        _RETRY_DELAY:  seconds to wait between attempts (default 5)
    """

    _MAX_ATTEMPTS: int = 2
    _RETRY_DELAY: int = 5

    def __init__(self, company_name: str, url: str):
        self.company_name = company_name
        self.url = url
        logger.debug("Initialized scraper for %s: %s", company_name, url)

    def scrape(self) -> List[Dict]:
        """Run scraping with automatic retry. Returns jobs found, or [] on total failure."""
        jobs = []
        for attempt in range(1, self._MAX_ATTEMPTS + 1):
            driver = None
            try:
                driver = create_chrome_driver()
                jobs = self._attempt_scrape(driver)
                if jobs:
                    break
                if attempt < self._MAX_ATTEMPTS:
                    logger.warning(
                        "%s: attempt %d returned 0 jobs, retrying in %ds...",
                        self.company_name, attempt, self._RETRY_DELAY,
                    )
                    time.sleep(self._RETRY_DELAY)
            except Exception as e:
                logger.error(
                    "%s: error on attempt %d: %s",
                    self.company_name, attempt, e, exc_info=True,
                )
                if attempt < self._MAX_ATTEMPTS:
                    time.sleep(self._RETRY_DELAY)
            finally:
                if driver:
                    driver.quit()

        logger.info("Scraped %d jobs from %s", len(jobs), self.company_name)
        return jobs

    @abstractmethod
    def _attempt_scrape(self, driver: webdriver.Chrome) -> List[Dict]:
        """Single scraping attempt using the provided driver.

        Must return a list of job dicts. Must not catch top-level exceptions —
        let them propagate so the base class retry logic can handle them.

        Each job dict must have:
            title, url, location, department, description, posted_date
        """
        pass
