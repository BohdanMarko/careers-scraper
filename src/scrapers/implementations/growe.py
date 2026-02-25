"""Scraper for Growe careers page."""

import logging
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from typing import List, Dict
from scrapers.base import BaseScraper

logger = logging.getLogger(__name__)


class GroweScraper(BaseScraper):
    """Scraper for Growe careers page."""

    def __init__(self, url: str = "https://growe.com/career"):
        super().__init__("Growe", url)

    def _attempt_scrape(self, driver) -> List[Dict]:
        """Single scraping attempt — load page, expand all jobs, extract cards."""
        driver.get(self.url)

        # Wait for initial job listings to appear
        WebDriverWait(driver, 30).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, 'a[class*="description__title"]'))
        )

        # Click "VIEW MORE" repeatedly until all jobs are loaded
        for _ in range(20):
            btns = driver.find_elements(By.CSS_SELECTOR, '[class*="vacancies-list__more"]')
            if not btns:
                break
            prev_count = len(driver.find_elements(By.CSS_SELECTOR, 'a[class*="description__title"]'))
            driver.execute_script('arguments[0].scrollIntoView(true)', btns[0])
            driver.execute_script('arguments[0].click()', btns[0])
            try:
                WebDriverWait(driver, 5).until(
                    lambda d, pc=prev_count: len(d.find_elements(By.CSS_SELECTOR, 'a[class*="description__title"]')) > pc
                )
            except Exception:
                break

        # Each job card: <a class="*description__title*"> inside a wrapper div
        # with a sibling <div class="*description__subtitle*"> holding dept + location
        title_links = driver.find_elements(By.CSS_SELECTOR, 'a[class*="description__title"]')

        jobs = []
        for link in title_links:
            try:
                href = link.get_attribute("href") or ""
                if not href.startswith("http"):
                    href = f"https://growe.com{href}"
                if "/career/vacancy/" not in href:
                    continue

                title = link.text.strip()
                if not title:
                    continue

                department = ""
                location = ""
                try:
                    # subtitle div is a sibling of the anchor inside the wrapper
                    wrapper = driver.execute_script("return arguments[0].parentElement", link)
                    subtitle_ps = wrapper.find_elements(
                        By.CSS_SELECTOR, '[class*="description__subtitle"] p'
                    )
                    # structure: [dept, ·, location]
                    texts = [p.text.strip() for p in subtitle_ps if p.text.strip() and p.text.strip() != "·"]
                    if len(texts) >= 2:
                        department = texts[0]
                        location = texts[1]
                    elif len(texts) == 1:
                        department = texts[0]
                except Exception as e:
                    logger.debug("Could not extract dept/location for job '%s': %s", title, e)

                jobs.append({
                    "title": title,
                    "url": href,
                    "location": location,
                    "department": department,
                    "description": "",
                    "posted_date": None,
                })
            except Exception as e:
                logger.warning("Growe: error parsing job element: %s", e)
                continue

        return jobs
