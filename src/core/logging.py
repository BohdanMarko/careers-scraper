"""Structured logging configuration for careers scraper."""

import logging
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional


def setup_logging(
    environment: str = "development",
    log_file: Optional[str] = None,
    log_rotation_max_bytes: int = 10 * 1024 * 1024,
    log_rotation_backup_count: int = 5,
):
    """
    Configure structured logging for the application.

    Args:
        environment: Environment name ("development" or "production")
        log_file: Optional file path for logging output
        log_rotation_max_bytes: Max size per log file before rotation
        log_rotation_backup_count: Number of rotated log files to keep

    Returns:
        Logger instance for the calling module
    """
    level = logging.DEBUG if environment == "development" else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    datefmt = "%Y-%m-%d %H:%M:%S"

    handlers = [logging.StreamHandler(sys.stdout)]
    if log_file:
        handlers.append(RotatingFileHandler(
            log_file,
            maxBytes=log_rotation_max_bytes,
            backupCount=log_rotation_backup_count,
            encoding="utf-8",
        ))

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
