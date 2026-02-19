"""Service for orchestrating job scraping and notifications."""

import logging
from datetime import datetime
from scrapers.implementations.uklon import UklonScraper
from scrapers.implementations.cdprojektred import CDProjektRedScraper
from scrapers.implementations.growe import GroweScraper
from notifications import TelegramNotifier
from config import settings, VacancyConfig

logger = logging.getLogger(__name__)

# Maps lowercase company name → scraper class
SCRAPER_REGISTRY = {
    "uklon": UklonScraper,
    "cd projekt red": CDProjektRedScraper,
    "growe": GroweScraper
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
        """Collect new matching jobs for a vacancy, then send one batched notification."""
        matched_jobs = []

        for job in jobs:
            url = job.get("url", "")
            if not url or url in self._seen_urls:
                continue

            self._seen_urls.add(url)

            if self._matches_keywords(job, vacancy.keywords):
                logger.info("New match: %s - %s", vacancy.name, job.get("title", ""))
                matched_jobs.append(job)

        if matched_jobs:
            self.notifier.send_company_jobs(vacancy.name, vacancy.url, matched_jobs)

    def _matches_keywords(self, job: dict, keywords: list[str]) -> bool:
        """Return True if any keyword appears in title, department, or description."""
        if not keywords:
            return False
        text = " ".join([
            str(job.get("title", "") or ""),
            str(job.get("department", "") or ""),
            str(job.get("description", "") or ""),
        ]).lower()
        return any(kw.lower() in text for kw in keywords)
