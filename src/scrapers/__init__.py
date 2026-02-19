"""Scraper base class and implementations."""

from scrapers.base import BaseScraper
from scrapers.implementations import (
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
