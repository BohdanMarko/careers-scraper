from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from database import Job, CompanyCareerPage, SessionLocal
from scrapers import UklonScraper, CDProjektRedScraper, GroweScraper
from telegram_notifier import TelegramNotifier
from config import settings


class ScraperService:
    """Main service for scraping job listings"""

    def __init__(self):
        self.notifier = TelegramNotifier()
        self.scrapers = {
            'uklon': UklonScraper(),
            'cd projekt red': CDProjektRedScraper(),
            'growe': GroweScraper()
        }

    def run_scraping_cycle(self):
        """Run a complete scraping cycle for all active companies"""
        print(f"[{datetime.now()}] Starting scraping cycle...")

        db = SessionLocal()
        try:
            # Get all active company pages
            companies = db.query(CompanyCareerPage).filter(
                CompanyCareerPage.is_active == True
            ).all()

            if not companies:
                print("No active company pages found. Adding default...")
                self._add_default_companies(db)
                companies = db.query(CompanyCareerPage).filter(
                    CompanyCareerPage.is_active == True
                ).all()

            for company in companies:
                self._scrape_company(company, db)

            print(f"[{datetime.now()}] Scraping cycle completed.")

        except Exception as e:
            print(f"Error during scraping cycle: {e}")
        finally:
            db.close()

    def _scrape_company(self, company: CompanyCareerPage, db: Session):
        """Scrape jobs from a specific company"""
        print(f"Scraping {company.company_name}...")

        scraper_key = company.company_name.lower()
        scraper = self.scrapers.get(scraper_key)

        if not scraper:
            print(f"No scraper found for {company.company_name}")
            return

        try:
            jobs = scraper.scrape()
            print(f"Found {len(jobs)} jobs at {company.company_name}")

            for job_data in jobs:
                self._process_job(job_data, company.company_name, db)

            # Update last scraped time
            company.last_scraped = datetime.utcnow()
            db.commit()

        except Exception as e:
            print(f"Error scraping {company.company_name}: {e}")
            db.rollback()

    def _process_job(self, job_data: dict, company_name: str, db: Session):
        """Process a single job listing"""
        # Check if job already exists
        existing_job = db.query(Job).filter(Job.url == job_data['url']).first()

        if existing_job:
            return  # Job already in database

        # Check if job matches keywords
        matches = any(
            keyword.lower() in " ".join([
                job_data.get('title', ''),
                job_data.get('description', ''),
                job_data.get('department', '')
            ]).lower()
            for keyword in settings.keywords_list
        )

        # Create new job entry
        new_job = Job(
            company=company_name,
            title=job_data.get('title', ''),
            location=job_data.get('location'),
            department=job_data.get('department'),
            url=job_data.get('url', ''),
            description=job_data.get('description'),
            posted_date=job_data.get('posted_date'),
            matches_keywords=matches,
            notified=False
        )

        db.add(new_job)
        db.commit()
        db.refresh(new_job)

        print(f"Added new job: {new_job.title}")

        # Send notification if job matches keywords
        if matches and not new_job.notified:
            try:
                self.notifier.send_job_notification_sync({
                    'company': company_name,
                    'title': new_job.title,
                    'location': new_job.location,
                    'department': new_job.department,
                    'url': new_job.url
                })
                new_job.notified = True
                db.commit()
            except Exception as e:
                print(f"Error sending notification: {e}")

    def _add_default_companies(self, db: Session):
        """Add default company career pages"""
        uklon = CompanyCareerPage(
            company_name="Uklon",
            url="https://careers.uklon.net/vacancies-ua",
            scraper_type="dynamic",
            is_active=True
        )
        cdpr = CompanyCareerPage(
            company_name="CD Projekt Red",
            url="https://www.cdprojektred.com/en/jobs",
            scraper_type="dynamic",
            is_active=True
        )
        growe = CompanyCareerPage(
            company_name="Growe",
            url="https://growe.com/career",
            scraper_type="dynamic",
            is_active=True
        )
        db.add(uklon)
        db.add(cdpr)
        db.add(growe)
        db.commit()
