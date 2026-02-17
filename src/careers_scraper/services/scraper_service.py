"""Service for orchestrating job scraping and notifications."""

import logging
from datetime import datetime
from careers_scraper.scrapers.implementations.uklon import UklonScraper
from careers_scraper.scrapers.implementations.cdprojektred import CDProjektRedScraper
from careers_scraper.scrapers.implementations.growe import GroweScraper
from careers_scraper.notifications import TelegramNotifier
from careers_scraper.config import settings, VacancyConfig

logger = logging.getLogger(__name__)

# Maps lowercase company name → scraper class
SCRAPER_REGISTRY = {
    "uklon": UklonScraper,
    "cd projekt red": CDProjektRedScraper,
    "growe": GroweScraper,
}


class ScraperService:
    """Orchestrates scraping cycles and sends Telegram notifications for new matching jobs."""

    def __init__(self):
        self.notifier = TelegramNotifier()
        self._seen_urls: set[str] = set()

        # Build scraper instances from config.yaml vacancies
        self._scrapers: list[tuple] = []  # (scraper, vacancy_config)
        for vacancy in settings.vacancies:
            scraper_class = SCRAPER_REGISTRY.get(vacancy.name.lower())
            if scraper_class:
                self._scrapers.append((scraper_class(url=vacancy.url), vacancy))
            else:
                logger.warning("No scraper found for '%s' — skipping", vacancy.name)

        logger.debug("ScraperService initialized with %d scrapers", len(self._scrapers))

    def run_scraping_cycle(self):
        """Run one scraping cycle across all configured vacancies."""
        logger.info("Scraping cycle started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for scraper, vacancy in self._scrapers:
            try:
                jobs = scraper.scrape()
                logger.info("Found %d jobs at %s", len(jobs), vacancy.name)
                self._process_jobs(vacancy, jobs)
            except Exception as e:
                logger.error("Error scraping %s: %s", vacancy.name, e, exc_info=True)

        logger.info("Scraping cycle finished")

    def _process_jobs(self, vacancy: VacancyConfig, jobs: list[dict]):
        """Send notifications for new jobs that match this vacancy's keywords."""
        for job in jobs:
            url = job.get("url", "")
            if not url or url in self._seen_urls:
                continue

            self._seen_urls.add(url)

            if self._matches_keywords(job, vacancy.keywords):
                logger.info("New match: %s - %s", vacancy.name, job.get("title", ""))
                try:
                    self.notifier.send_job_notification_sync({
                        "company": vacancy.name,
                        "title": job.get("title", ""),
                        "location": job.get("location", ""),
                        "department": job.get("department", ""),
                        "url": url,
                    })
                except Exception as e:
                    logger.error("Failed to send notification: %s", e)

    def _matches_keywords(self, job: dict, keywords: list[str]) -> bool:
        """Return True if any keyword appears in title, department, or description."""
        if not keywords:
            return False
        text = " ".join([
            job.get("title", ""),
            job.get("department", ""),
            job.get("description", ""),
        ]).lower()
        return any(kw in text for kw in keywords)
