"""Scraper base class and implementations."""

from careers_scraper.scrapers.base import BaseScraper
from careers_scraper.scrapers.implementations import (
    UklonScraper,
    CDProjektRedScraper,
    GroweScraper,
)

__all__ = [
    "BaseScraper",
    "UklonScraper",
    "CDProjektRedScraper",
    "GroweScraper",
]
