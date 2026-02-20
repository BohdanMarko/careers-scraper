"""Entry point for careers-scraper."""

import sys
import time
import argparse
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.logging import setup_logging
from scheduler import JobScheduler
from services.scraper_service import ScraperService
from config import settings

logger = setup_logging(
    settings.environment,
    log_file="log.txt",
    log_rotation_max_bytes=settings.log_rotation.max_bytes,
    log_rotation_backup_count=settings.log_rotation.backup_count,
)


def main():
    parser = argparse.ArgumentParser(description="Careers Scraper")
    parser.add_argument(
        "--single-run",
        action="store_true",
        help="Run one scraping cycle and exit instead of scheduling periodic runs",
    )
    args = parser.parse_args()

    logger.info("=" * 50)
    logger.info("Careers Scraper Starting...")
    logger.info("=" * 50)

    if args.single_run:
        ScraperService().run_scraping_cycle()
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
