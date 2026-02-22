"""Entry point for careers-scraper."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from core.logging import setup_logging
from services.scraper_service import ScraperService
from config import settings

logger = setup_logging(
    settings.environment,
    log_file="log.txt",
    log_rotation_max_bytes=settings.log_rotation.max_bytes,
    log_rotation_backup_count=settings.log_rotation.backup_count,
)


def main():
    logger.info("Careers Scraper Starting...")
    ScraperService().run_scraping_cycle()


if __name__ == "__main__":
    main()
