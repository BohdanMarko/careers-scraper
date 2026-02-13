"""Main entry point for careers scraper application."""

import logging
import uvicorn
from careers_scraper.core.logging import setup_logging
from careers_scraper.scheduler import JobScheduler
from careers_scraper.web import app
from careers_scraper.config import settings

# Set up logging first
logger = setup_logging(settings.environment)


def run_web_server():
    """Run the FastAPI web server."""
    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info"
    )


def main():
    """Main entry point for the application."""
    logger.info("=" * 50)
    logger.info("Careers Scraper Starting...")
    logger.info("=" * 50)

    # Database initialization handled automatically by SQLAlchemy
    logger.info("Database will be created automatically on first run")

    # Start scheduler in background
    logger.info("Starting job scheduler...")
    scheduler = JobScheduler()
    scheduler.start()

    # Start web server (blocking)
    logger.info(
        f"Starting web server at http://{settings.web_host}:{settings.web_port}"
    )
    logger.info("=" * 50)

    try:
        run_web_server()
    except KeyboardInterrupt:
        logger.info("\nShutting down...")
        scheduler.stop()
        logger.info("Goodbye!")


if __name__ == "__main__":
    main()
