"""Scraper for Uklon careers page."""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict
from scrapers.base import BaseScraper, create_chrome_driver

logger = logging.getLogger(__name__)


class UklonScraper(BaseScraper):
    """Scraper for Uklon careers page."""

    def __init__(self, url: str = "https://careers.uklon.net/vacancies-ua"):
        super().__init__("Uklon", url)

    def scrape(self) -> List[Dict]:
        """Scrape job listings from Uklon careers page."""
        jobs = []

        driver = None
        try:
            driver = create_chrome_driver()
            driver.get(self.url)
            WebDriverWait(driver, 15).until(EC.presence_of_all_elements_located((By.CSS_SELECTOR, "div.w-grid__item-panel")))

            # Scroll to trigger lazy loading
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")

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
