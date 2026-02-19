"""Main entry point for careers scraper application."""

import time
from careers_scraper.core.logging import setup_logging
from careers_scraper.scheduler import JobScheduler
from careers_scraper.config import settings
from careers_scraper.services.scraper_service import ScraperService

logger = setup_logging(settings.environment, log_file="log.txt")


def main():
    logger.info("=" * 50)
    logger.info("Careers Scraper Starting...")
    logger.info("=" * 50)

    if True:
        scraper_service = ScraperService()
        scraper_service.run_scraping_cycle()
        return

    scheduler = JobScheduler()
    scheduler.start()

    try:
        while True:
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Shutting down...")
        scheduler.stop()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
