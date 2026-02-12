from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.chrome.service import Service
from webdriver_manager.chrome import ChromeDriverManager
from typing import List, Dict
import time
from .base_scraper import BaseScraper


class GroweScraper(BaseScraper):
    """Scraper for Growe careers page"""

    def __init__(self):
        super().__init__("Growe", "https://growe.com/career")

    def scrape(self) -> List[Dict]:
        """Scrape job listings from Growe careers page"""
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

            # Wait for page to load
            time.sleep(5)

            # Try to click "view more" button if it exists to load all jobs
            try:
                view_more_button = driver.find_element(By.XPATH, "//*[contains(text(), 'view more') or contains(text(), 'View more')]")
                view_more_button.click()
                time.sleep(2)
            except:
                pass  # Button might not exist if all jobs are already displayed

            # Find job listings - try multiple selector strategies
            job_elements = []

            # Try different selectors
            selectors = [
                "a[href*='/career/vacancy/']",
                "[class*='vacancy']",
                "[class*='job-item']",
                "[class*='position']"
            ]

            for selector in selectors:
                try:
                    job_elements = driver.find_elements(By.CSS_SELECTOR, selector)
                    if job_elements:
                        break
                except:
                    continue

            if not job_elements:
                print("No job elements found with standard selectors, trying to extract from page structure")
                # Fallback: try to find all links containing /career/vacancy/
                job_elements = driver.find_elements(By.XPATH, "//a[contains(@href, '/career/vacancy/')]")

            for job_elem in job_elements:
                try:
                    # Get the job URL
                    url = job_elem.get_attribute("href") or ""

                    # Try to get text content
                    text_content = job_elem.text.strip()

                    # Parse the text content
                    # Expected format: "Job Title" or "Job Title\nDepartment · Location"
                    lines = text_content.split('\n')

                    title = lines[0] if lines else ""
                    department = ""
                    location = ""

                    if len(lines) > 1:
                        # Try to parse "Department · Location" format
                        meta_info = lines[1].split('·')
                        if len(meta_info) >= 2:
                            department = meta_info[0].strip()
                            location = meta_info[1].strip()
                        elif len(meta_info) == 1:
                            # Could be either department or location
                            department = meta_info[0].strip()

                    job = {
                        'title': title,
                        'location': location,
                        'department': department,
                        'url': url if url.startswith('http') else f"https://growe.com{url}",
                        'description': text_content,
                        'posted_date': None
                    }

                    if job['title'] and job['url']:  # Only add if we have title and URL
                        jobs.append(job)
                except Exception as e:
                    print(f"Error parsing job element: {e}")
                    continue

        except Exception as e:
            print(f"Error scraping Growe careers page: {e}")
        finally:
            if driver:
                driver.quit()

        return jobs
