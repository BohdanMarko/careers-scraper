#!/usr/bin/env python
"""
Test script for debugging individual scrapers
Usage: python test_scraper.py [scraper_name]
Example: python test_scraper.py cdpr
"""

import sys
from scrapers import UklonScraper, CDProjektRedScraper, GroweScraper


def test_uklon():
    """Test Uklon scraper"""
    print("Testing Uklon scraper...")
    scraper = UklonScraper()
    jobs = scraper.scrape()
    print(f"\nFound {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:5], 1):  # Show first 5
        print(f"\n{i}. {job['title']}")
        print(f"   Location: {job['location']}")
        print(f"   Department: {job['department']}")
        print(f"   URL: {job['url']}")


def test_cdpr():
    """Test CD Projekt Red scraper"""
    print("Testing CD Projekt Red scraper...")
    scraper = CDProjektRedScraper()
    jobs = scraper.scrape()
    print(f"\nFound {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:5], 1):  # Show first 5
        print(f"\n{i}. {job['title']}")
        print(f"   Location: {job['location']}")
        print(f"   Department: {job['department']}")
        print(f"   Description: {job['description']}")
        print(f"   URL: {job['url']}")


def test_growe():
    """Test Growe scraper"""
    print("Testing Growe scraper...")
    scraper = GroweScraper()
    jobs = scraper.scrape()
    print(f"\nFound {len(jobs)} jobs:")
    for i, job in enumerate(jobs[:5], 1):  # Show first 5
        print(f"\n{i}. {job['title']}")
        print(f"   Location: {job['location']}")
        print(f"   Department: {job['department']}")
        print(f"   URL: {job['url']}")


def test_all():
    """Test all scrapers"""
    print("=" * 60)
    test_uklon()
    print("\n" + "=" * 60 + "\n")
    test_cdpr()
    print("\n" + "=" * 60 + "\n")
    test_growe()
    print("\n" + "=" * 60)


if __name__ == "__main__":
    scrapers = {
        'uklon': test_uklon,
        'cdpr': test_cdpr,
        'cdprojektred': test_cdpr,
        'growe': test_growe,
        'all': test_all
    }

    if len(sys.argv) > 1:
        scraper_name = sys.argv[1].lower()
        if scraper_name in scrapers:
            scrapers[scraper_name]()
        else:
            print(f"Unknown scraper: {scraper_name}")
            print(f"Available: {', '.join(scrapers.keys())}")
    else:
        # Default: test all
        test_all()
