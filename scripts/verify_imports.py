"""Verify all imports work after restructuring."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

def test_imports():
    """Test all major imports from the package."""
    results = []

    # Test config imports
    try:
        from careers_scraper.config import settings
        results.append(("[OK]", "Config: settings"))
    except Exception as e:
        results.append(("[FAIL]", f"Config: settings - {e}"))

    # Test database imports
    try:
        from careers_scraper.db import Base, Job, CompanyCareerPage
        results.append(("[OK]", "Database: Base, Job, CompanyCareerPage"))
    except Exception as e:
        results.append(("[FAIL]", f"Database models - {e}"))

    try:
        from careers_scraper.db import engine, SessionLocal, get_db
        results.append(("[OK]", "Database: engine, SessionLocal, get_db"))
    except Exception as e:
        results.append(("[FAIL]", f"Database session - {e}"))

    try:
        from careers_scraper.db import JobRepository, CompanyRepository
        results.append(("[OK]", "Database: JobRepository, CompanyRepository"))
    except Exception as e:
        results.append(("[FAIL]", f"Database repositories - {e}"))

    # Test scraper imports
    try:
        from careers_scraper.scrapers import BaseScraper
        results.append(("[OK]", "Scrapers: BaseScraper"))
    except Exception as e:
        results.append(("[FAIL]", f"Scrapers: BaseScraper - {e}"))

    try:
        from careers_scraper.scrapers import (
            UklonScraper,
            CDProjektRedScraper,
            GroweScraper
        )
        results.append(("[OK]", "Scrapers: UklonScraper, CDProjektRedScraper, GroweScraper"))
    except Exception as e:
        results.append(("[FAIL]", f"Scraper implementations - {e}"))

    # Test service imports
    try:
        from careers_scraper.services import ScraperService
        results.append(("[OK]", "Services: ScraperService"))
    except Exception as e:
        results.append(("[FAIL]", f"Services: ScraperService - {e}"))

    try:
        from careers_scraper.notifications import TelegramNotifier
        results.append(("[OK]", "Notifications: TelegramNotifier"))
    except Exception as e:
        results.append(("[FAIL]", f"Notifications: TelegramNotifier - {e}"))

    # Test web imports
    try:
        from careers_scraper.web import app
        results.append(("[OK]", "Web: app"))
    except Exception as e:
        results.append(("[FAIL]", f"Web: app - {e}"))

    # Test core imports
    try:
        from careers_scraper.core.logging import setup_logging
        results.append(("[OK]", "Core: setup_logging"))
    except Exception as e:
        results.append(("[FAIL]", f"Core: setup_logging - {e}"))

    # Test scheduler imports
    try:
        from careers_scraper.scheduler import JobScheduler
        results.append(("[OK]", "Scheduler: JobScheduler"))
    except Exception as e:
        results.append(("[FAIL]", f"Scheduler: JobScheduler - {e}"))

    # Test main import
    try:
        from careers_scraper.main import main
        results.append(("[OK]", "Main: main"))
    except Exception as e:
        results.append(("[FAIL]", f"Main: main - {e}"))

    return results


if __name__ == "__main__":
    print("=" * 60)
    print("IMPORT VERIFICATION RESULTS")
    print("=" * 60)

    results = test_imports()

    success_count = sum(1 for status, _ in results if status == "[OK]")
    total_count = len(results)

    for status, message in results:
        print(f"{status} {message}")

    print("=" * 60)
    print(f"Results: {success_count}/{total_count} imports successful")
    print("=" * 60)

    sys.exit(0 if success_count == total_count else 1)
