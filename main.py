import uvicorn
from database import init_db
from scheduler import JobScheduler
from web_app import app
from config import settings
import threading


def run_web_server():
    """Run the FastAPI web server"""
    uvicorn.run(
        app,
        host=settings.web_host,
        port=settings.web_port,
        log_level="info"
    )


def main():
    """Main entry point"""
    print("=" * 50)
    print("Careers Scraper Starting...")
    print("=" * 50)

    # Initialize database
    print("Initializing database...")
    init_db()

    # Start scheduler in background
    print("Starting job scheduler...")
    scheduler = JobScheduler()
    scheduler.start()

    # Start web server (blocking)
    print(f"Starting web server at http://{settings.web_host}:{settings.web_port}")
    print("=" * 50)

    try:
        run_web_server()
    except KeyboardInterrupt:
        print("\nShutting down...")
        scheduler.stop()
        print("Goodbye!")


if __name__ == "__main__":
    main()
