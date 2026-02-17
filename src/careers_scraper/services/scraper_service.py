"""Service for orchestrating job scraping and notifications."""

import logging
from datetime import datetime
from careers_scraper.scrapers import UklonScraper, CDProjektRedScraper, GroweScraper
from careers_scraper.notifications import TelegramNotifier
from careers_scraper.config import settings

logger = logging.getLogger(__name__)


class ScraperService:
    """Orchestrates scraping cycles and sends Telegram notifications for new matching jobs."""

    def __init__(self):
        self.notifier = TelegramNotifier()
        self.scrapers = [
            UklonScraper(),
            CDProjektRedScraper(),
            GroweScraper(),
        ]
        self._seen_urls: set[str] = set()
        logger.debug("ScraperService initialized with %d scrapers", len(self.scrapers))

    def run_scraping_cycle(self):
        """Run one scraping cycle across all companies."""
        logger.info("Scraping cycle started at %s", datetime.now().strftime("%Y-%m-%d %H:%M:%S"))

        for scraper in self.scrapers:
            try:
                jobs = scraper.scrape()
                logger.info("Found %d jobs at %s", len(jobs), scraper.company_name)
                self._process_jobs(scraper.company_name, jobs)
            except Exception as e:
                logger.error("Error scraping %s: %s", scraper.company_name, e, exc_info=True)

        logger.info("Scraping cycle finished")

    def _process_jobs(self, company_name: str, jobs: list[dict]):
        """Check jobs for keyword matches and send notifications for new ones."""
        for job in jobs:
            url = job.get("url", "")
            if not url or url in self._seen_urls:
                continue

            self._seen_urls.add(url)

            if self._matches_keywords(job):
                logger.info("New match: %s - %s", company_name, job.get("title", ""))
                try:
                    self.notifier.send_job_notification_sync({
                        "company": company_name,
                        "title": job.get("title", ""),
                        "location": job.get("location", ""),
                        "department": job.get("department", ""),
                        "url": url,
                    })
                except Exception as e:
                    logger.error("Failed to send notification: %s", e)

    def _matches_keywords(self, job: dict) -> bool:
        """Return True if any keyword appears in title, department, or description."""
        text = " ".join([
            job.get("title", ""),
            job.get("department", ""),
            job.get("description", ""),
        ]).lower()
        return any(kw in text for kw in settings.keywords_list)
