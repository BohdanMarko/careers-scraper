"""Structured logging configuration for careers scraper."""

import logging
import sys
from typing import Optional


def setup_logging(environment: str = "development", log_file: Optional[str] = None):
    """
    Configure structured logging for the application.

    Args:
        environment: Environment name ("development" or "production")
        log_file: Optional file path for logging output

    Returns:
        Logger instance for the calling module
    """
    level = logging.DEBUG if environment == "development" else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(logging.FileHandler(log_file))

    logging.basicConfig(
        level=level,
        format=fmt,
        datefmt=datefmt,
        handlers=handlers,
        force=True  # Override any existing configuration
    )

    # Suppress noisy third-party libraries
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)

    logger = logging.getLogger(__name__)
    logger.info(f"Logging configured for {environment} environment")
    return logger
