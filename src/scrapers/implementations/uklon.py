"""Scraper for Uklon careers page."""

import logging
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from typing import List, Dict
import time
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class UklonScraper(BaseScraper):
    """Scraper for Uklon careers page."""

    def __init__(self, url: str = "https://careers.uklon.net/vacancies-ua"):
        super().__init__("Uklon", url)

    def scrape(self) -> List[Dict]:
        """Scrape job listings from Uklon careers page."""
        jobs = []

        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")

        driver = None
        try:
            driver = webdriver.Chrome(options=chrome_options)
            driver.get(self.url)
            time.sleep(8)

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            time.sleep(3)

            # Each job is a card: div.w-grid__item-panel
            cards = driver.find_elements(By.CSS_SELECTOR, "div.w-grid__item-panel")

            for card in cards:
                try:
                    title = card.find_element(
                        By.CSS_SELECTOR, "p.ui-heading span.w-text-content"
                    ).text.strip()

                    location = card.find_element(
                        By.CSS_SELECTOR, "p.ui-text span.w-text-content"
                    ).text.strip()

                    link_el = card.find_element(By.CSS_SELECTOR, "a[data-component='button']")
                    href = link_el.get_attribute("href") or ""
                    if href and not href.startswith("http"):
                        href = "https://careers.uklon.net" + href

                    if not title or not href:
                        continue

                    jobs.append({
                        "title": title,
                        "url": href,
                        "location": location,
                        "department": "",
                        "description": "",
                        "posted_date": None,
                    })
                except Exception as e:
                    logger.debug("Skipping non-job card: %s", e)
                    continue

        except Exception as e:
            logger.error("Error scraping Uklon careers page: %s", e)
        finally:
            if driver:
                driver.quit()

        logger.info("Scraped %d jobs from Uklon", len(jobs))
        return jobs
