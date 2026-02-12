"""Main service for orchestrating job scraping operations."""

import logging
from datetime import datetime
from typing import List
from sqlalchemy.orm import Session
from careers_scraper.db.models import Job, CompanyCareerPage
from careers_scraper.db.session import SessionLocal
from careers_scraper.scrapers import UklonScraper, CDProjektRedScraper, GroweScraper
from careers_scraper.notifications import TelegramNotifier
from careers_scraper.config import settings

logger = logging.getLogger(__name__)


class ScraperService:
    """Main service for scraping job listings from configured companies."""

    def __init__(self):
        """Initialize scraper service with notifier and scraper registry."""
        self.notifier = TelegramNotifier()
        # Hard-coded scraper registry (Phase 2 will add @register_scraper decorator)
        self.scrapers = {
            'uklon': UklonScraper(),
            'cd projekt red': CDProjektRedScraper(),
            'growe': GroweScraper()
        }
        logger.debug("ScraperService initialized with 3 scrapers")

    def run_scraping_cycle(self):
        """Run a complete scraping cycle for all active companies."""
        logger.info(f"Starting scraping cycle at {datetime.now()}")

        db = SessionLocal()
        try:
            # Get all active company pages
            companies = db.query(CompanyCareerPage).filter(
                CompanyCareerPage.is_active == True
            ).all()

            if not companies:
                logger.info("No active company pages found. Adding defaults...")
                self._add_default_companies(db)
                companies = db.query(CompanyCareerPage).filter(
                    CompanyCareerPage.is_active == True
                ).all()

            for company in companies:
                self._scrape_company(company, db)

            logger.info(f"Scraping cycle completed at {datetime.now()}")

        except Exception as e:
            logger.error(f"Error during scraping cycle: {e}", exc_info=True)
        finally:
            db.close()

    def _scrape_company(self, company: CompanyCareerPage, db: Session):
        """
        Scrape jobs from a specific company.

        Args:
            company: CompanyCareerPage instance
            db: Database session
        """
        logger.info(f"Scraping {company.company_name}...")

        scraper_key = company.company_name.lower()
        scraper = self.scrapers.get(scraper_key)

        if not scraper:
            logger.warning(f"No scraper found for {company.company_name}")
            return

        try:
            jobs = scraper.scrape()
            logger.info(f"Found {len(jobs)} jobs at {company.company_name}")

            for job_data in jobs:
                self._process_job(job_data, company.company_name, db)

            # Update last scraped time
            company.last_scraped = datetime.utcnow()
            db.commit()

        except Exception as e:
            logger.error(f"Error scraping {company.company_name}: {e}", exc_info=True)
            db.rollback()

    def _process_job(self, job_data: dict, company_name: str, db: Session):
        """
        Process a single job listing.

        Args:
            job_data: Dictionary containing job information
            company_name: Name of the company
            db: Database session
        """
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

        logger.info(f"Added new job: {company_name} - {new_job.title}")

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
                logger.error(f"Error sending notification: {e}", exc_info=True)

    def _add_default_companies(self, db: Session):
        """
        Add default company career pages to database.

        Args:
            db: Database session
        """
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
        logger.info("Added 3 default companies to database")
