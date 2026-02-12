"""Job scheduler for periodic scraping operations."""

import logging
from apscheduler.schedulers.background import BackgroundScheduler
from careers_scraper.services import ScraperService
from careers_scraper.config import settings

logger = logging.getLogger(__name__)


class JobScheduler:
    """Scheduler for periodic job scraping."""

    def __init__(self):
        """Initialize scheduler and scraper service."""
        self.scheduler = BackgroundScheduler()
        self.scraper_service = ScraperService()
        logger.debug("JobScheduler initialized")

    def start(self):
        """Start the scheduler and run initial scraping cycle."""
        # Run immediately on start
        self.scraper_service.run_scraping_cycle()

        # Schedule periodic runs
        self.scheduler.add_job(
            self.scraper_service.run_scraping_cycle,
            'interval',
            minutes=settings.scrape_interval,
            id='scraping_job',
            replace_existing=True
        )

        self.scheduler.start()
        logger.info(
            f"Scheduler started. Scraping every {settings.scrape_interval} minutes."
        )

    def stop(self):
        """Stop the scheduler gracefully."""
        self.scheduler.shutdown()
        logger.info("Scheduler stopped.")
