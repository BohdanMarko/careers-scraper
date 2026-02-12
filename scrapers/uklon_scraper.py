from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict
import time
from .base_scraper import BaseScraper


class UklonScraper(BaseScraper):
    """Scraper for Uklon careers page"""

    def __init__(self):
        super().__init__("Uklon", "https://careers.uklon.net/vacancies-ua")

    def scrape(self) -> List[Dict]:
        """Scrape job listings from Uklon careers page"""
        jobs = []

        # Set up headless Chrome
        chrome_options = Options()
        chrome_options.add_argument("--headless")
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")

        driver = None
        try:
            driver = webdriver.Chrome(
                service=Service(ChromeDriverManager().install()),
                options=chrome_options
            )

            driver.get(self.url)

            # Wait for page to load (adjust selector based on actual page structure)
            time.sleep(5)  # Initial wait for dynamic content

            # TODO: Update these selectors based on actual page structure
            # This is a placeholder - you'll need to inspect the actual page
            # and update the selectors accordingly

            try:
                job_elements = driver.find_elements(By.CSS_SELECTOR, "[class*='vacancy'], [class*='job']")

                for job_elem in job_elements:
                    try:
                        job = {
                            'title': self._safe_get_text(job_elem, "[class*='title']"),
                            'location': self._safe_get_text(job_elem, "[class*='location']"),
                            'department': self._safe_get_text(job_elem, "[class*='department']"),
                            'url': self._safe_get_link(job_elem),
                            'description': self._safe_get_text(job_elem, "[class*='description']"),
                            'posted_date': None
                        }

                        if job['title']:  # Only add if we found a title
                            jobs.append(job)
                    except Exception as e:
                        print(f"Error parsing job element: {e}")
                        continue

            except Exception as e:
                print(f"Error finding job elements: {e}")

        except Exception as e:
            print(f"Error scraping Uklon careers page: {e}")
        finally:
            if driver:
                driver.quit()

        return jobs

    def _safe_get_text(self, parent_element, selector: str) -> str:
        """Safely get text from an element"""
        try:
            element = parent_element.find_element(By.CSS_SELECTOR, selector)
            return element.text.strip()
        except:
            return ""

    def _safe_get_link(self, element) -> str:
        """Safely get link from an element"""
        try:
            link = element.find_element(By.TAG_NAME, "a")
            href = link.get_attribute("href")
            return href if href else ""
        except:
            return ""
