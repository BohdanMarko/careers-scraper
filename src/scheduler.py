"""Periodic scraping scheduler."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from services import ScraperService
from config import settings

logger = logging.getLogger(__name__)


class JobScheduler:
    """Runs scraping cycles on a fixed interval using APScheduler."""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scraper_service = ScraperService()

    def start(self):
        """Run an immediate scraping cycle then schedule periodic runs."""
        self.scraper_service.run_scraping_cycle()

        self.scheduler.add_job(
            self.scraper_service.run_scraping_cycle,
            "interval",
            minutes=settings.scrape_interval,
            id="scraping_job",
            replace_existing=True,
            max_instances=1,
        )
        self.scheduler.start()
        logger.info("Scheduler started. Scraping every %d minutes.", settings.scrape_interval)

    def stop(self):
        """Shut down the scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")
