from apscheduler.schedulers.background import BackgroundScheduler
from scraper_service import ScraperService
from config import settings


class JobScheduler:
    """Scheduler for periodic job scraping"""

    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.scraper_service = ScraperService()

    def start(self):
        """Start the scheduler"""
        # Run immediately on start
        self.scraper_service.run_scraping_cycle()

        # Schedule periodic runs
        self.scheduler.add_job(
            self.scraper_service.run_scraping_cycle,
            'interval',
            minutes=settings.scrape_interval,
            id='scraping_job',
            replace_existing=True
        )

        self.scheduler.start()
        print(f"Scheduler started. Scraping every {settings.scrape_interval} minutes.")

    def stop(self):
        """Stop the scheduler"""
        self.scheduler.shutdown()
        print("Scheduler stopped.")
