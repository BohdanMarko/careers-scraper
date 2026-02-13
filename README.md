# Careers Scraper

A Python-based web scraper that monitors career pages of multiple companies, filters jobs by keywords, and sends Telegram notifications for matching positions.

## Features

- 🔍 **Multi-company scraping** - Monitors multiple career pages with different HTML structures
- 🎯 **Keyword filtering** - Filters jobs by customizable keywords or phrases
- 📱 **Telegram notifications** - Real-time alerts for matching positions
- 🌐 **Web dashboard** - Beautiful, responsive interface to view all jobs
- ⏰ **Automated scheduling** - Configurable periodic checks (default: hourly)
- 💾 **Database storage** - SQLite for local development, PostgreSQL-ready for cloud deployment
- ☁️ **Cloud-ready** - Prepared for Azure/AWS deployment

### Supported Companies

- [Uklon](https://careers.uklon.net/vacancies-ua)
- [CD Projekt Red](https://www.cdprojektred.com/en/jobs?studio=poland)
- [Growe](https://growe.com/career)

Adding new companies is designed to be simple and extensible.

## Project Structure

```
careers-scraper/
├── src/careers_scraper/           # Main application package
│   ├── config.py                  # Configuration management (env variables)
│   ├── main.py                    # Application entry point
│   ├── scheduler.py               # Job scheduling logic
│   ├── core/                      # Core utilities
│   │   └── logging.py            # Logging configuration
│   ├── db/                        # Database layer
│   │   ├── models.py             # SQLAlchemy models (Job, CompanyCareerPage)
│   │   ├── engine.py             # Database engine
│   │   ├── session.py            # Session management
│   │   └── repositories/         # Data access layer
│   ├── scrapers/                  # Scraping logic
│   │   ├── base.py               # BaseScraper abstract class
│   │   └── implementations/      # Company-specific scrapers
│   │       ├── uklon.py
│   │       ├── cdprojektred.py
│   │       └── growe.py
│   ├── services/                  # Business logic
│   │   └── scraper_service.py    # Orchestrates scraping
│   ├── notifications/             # Notification channels
│   │   └── telegram.py           # Telegram bot integration
│   └── web/                       # Web interface
│       ├── app.py                # FastAPI application
│       └── static/               # HTML/CSS/JS files
├── scripts/                       # Utility scripts
│   ├── init_db.py                # Database initialization
│   ├── migrations/               # Manual SQL migrations
│   └── verify_imports.py         # Import verification
├── tests/                         # Test suite
├── docs/ai/                       # AI-assisted documentation
├── main.py                        # Entry point wrapper
├── test_scraper.py               # Manual scraper testing tool
├── requirements.txt               # Python dependencies
├── .env.example                   # Environment variables template
└── README.md                      # This file
```

## Local Setup & Development

### Prerequisites

- **Python 3.13** (or 3.12+)
- **Google Chrome** or **Chromium** (for Selenium-based scrapers)
- **Telegram Bot** (see setup instructions below)

### 1. Clone & Navigate

```bash
cd D:\Projects\careers-scraper
```

### 2. Create Virtual Environment

**Windows (recommended):**
```bash
# Using Python 3.13
python -m venv .venv

# Activate venv
.venv\Scripts\activate
```

**Git Bash / Unix-like:**
```bash
source .venv/Scripts/activate
```

### 3. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

**Current dependencies:**
- beautifulsoup4==4.12.3
- requests==2.31.0
- selenium==4.17.2
- python-telegram-bot==21.0.1
- fastapi==0.115.0
- uvicorn==0.27.1
- sqlalchemy==2.0.36
- apscheduler==3.10.4
- python-dotenv==1.0.1
- pydantic==2.10.5
- pydantic-settings==2.7.1
- webdriver-manager==4.0.1

### 4. Configure Environment Variables

Copy the example file and edit it:

```bash
cp .env.example .env
```

Edit `.env` with your settings:

```env
# Telegram Bot Configuration
TELEGRAM_BOT_TOKEN=your_telegram_bot_token_here
TELEGRAM_CHAT_ID=your_telegram_chat_id_here

# Search Keywords (comma-separated)
SEARCH_KEYWORDS=python,backend,developer,engineer

# Database
DATABASE_URL=sqlite:///./careers.db

# Web Interface
WEB_HOST=0.0.0.0
WEB_PORT=8000

# Scraping Schedule (in minutes)
SCRAPE_INTERVAL=60
```

### 5. Get Telegram Bot Credentials

#### Get Bot Token:
1. Open Telegram and talk to [@BotFather](https://t.me/botfather)
2. Send `/newbot` and follow the prompts
3. Copy the token and paste it as `TELEGRAM_BOT_TOKEN` in `.env`

#### Get Your Chat ID:
1. Talk to [@userinfobot](https://t.me/userinfobot)
2. Copy your Chat ID and paste it as `TELEGRAM_CHAT_ID` in `.env`

**Or use this existing bot:**
- Bot: [@CareersScraperBot](https://t.me/CareersScraperBot)
- API Docs: https://core.telegram.org/bots/api

### 6. Initialize Database

Run the initialization script:

```bash
python scripts/init_db.py
```

This creates the SQLite database with required tables:
- `jobs` - Stores scraped job postings
- `company_career_pages` - Company configuration

### 7. Run the Application

```bash
python main.py
```

This will:
- ✅ Initialize logging
- ✅ Start the job scheduler (scrapes based on `SCRAPE_INTERVAL`)
- ✅ Launch the web dashboard at http://localhost:8000

### 8. Access the Web Dashboard

Open your browser and navigate to:
```
http://localhost:8000
```

Features:
- View all scraped jobs
- Filter by company or keyword matches
- Real-time statistics
- Auto-refreshes every 30 seconds

## Development & Testing

### Test Individual Scrapers

```bash
# Test a specific scraper
python test_scraper.py uklon
python test_scraper.py cdprojektred
python test_scraper.py growe

# Test all scrapers
python test_scraper.py all
```

### Run with Debugging

```bash
# Activate venv first
.venv\Scripts\activate

# Run with Python directly
python main.py
```

### Database Management

**View database:**
```bash
sqlite3 careers.db
.tables
SELECT * FROM jobs;
.exit
```

**Reset database:**
```bash
rm careers.db
python scripts/init_db.py
```

## Adding New Career Pages

### 1. Create a New Scraper

Create a new file in `src/careers_scraper/scrapers/implementations/`:

```python
# src/careers_scraper/scrapers/implementations/mycompany.py
from ..base import BaseScraper

class MyCompanyScraper(BaseScraper):
    def __init__(self):
        super().__init__(
            company_name="MyCompany",
            career_url="https://careers.mycompany.com"
        )

    def scrape(self) -> list:
        """Implement scraping logic here."""
        jobs = []
        # Your scraping logic
        return jobs
```

### 2. Register the Scraper

Add it to `src/careers_scraper/scrapers/__init__.py`:

```python
from .implementations.mycompany import MyCompanyScraper
```

### 3. Add to Service

Update `src/careers_scraper/services/scraper_service.py` to include your scraper.

### 4. Add Company to Database

Either manually via SQL or add it through the scraper service.

## Customization

### Change Scraping Interval

Edit `.env`:
```env
SCRAPE_INTERVAL=120  # Check every 2 hours
```

### Add Keywords

Edit `.env`:
```env
SEARCH_KEYWORDS=python,django,fastapi,react,typescript,backend,senior
```

Keywords are case-insensitive and matched against job titles and descriptions.

### Change Web Server Port

Edit `.env`:
```env
WEB_PORT=3000
```

## Cloud Deployment

This project is designed for cloud deployment:

### Azure (Primary Target)
- **Hosting:** Azure Container Apps
- **Database:** Azure Database for PostgreSQL
- **Secrets:** Azure Key Vault
- **Estimated cost:** ~$25-35/month

### AWS (Alternative)
- **Hosting:** ECS Fargate
- **Database:** RDS PostgreSQL
- **Secrets:** AWS Secrets Manager

See `docs/ai/phase-4-cloud.spec.md` for detailed deployment plans.

## Architecture Notes

- **Single-process monolith** - Web server + scheduler run in one process
- **Scraping methods:**
  - Static pages: `requests` + `BeautifulSoup`
  - Dynamic pages: `Selenium` + `webdriver-manager`
- **Database:** SQLite for local, PostgreSQL for production
- **Logging:** Structured logging via `core/logging.py`
- **No Alembic** - Using simple SQL migration scripts for database changes

## Troubleshooting

### ChromeDriver Issues

If Selenium fails to start:
1. Ensure Chrome/Chromium is installed
2. `webdriver-manager` will auto-download the correct ChromeDriver version
3. Check firewall/antivirus isn't blocking the download

### Import Errors

If you get import errors:
```bash
# Make sure venv is activated
.venv\Scripts\activate

# Reinstall dependencies
pip install -r requirements.txt
```

### Database Locked

If SQLite shows "database is locked":
- Only one process can write at a time
- Stop any running instances of the app
- For concurrent access, consider PostgreSQL

### Telegram Notifications Not Working

1. Verify bot token is correct in `.env`
2. Verify chat ID is correct
3. Ensure you've started a conversation with the bot first
4. Check network connectivity

## Project Roadmap

See `docs/ai/master-plan.md` for the complete roadmap.

**Completed:**
- ✅ Basic scraping infrastructure
- ✅ Telegram notifications
- ✅ Web dashboard
- ✅ Database storage
- ✅ Multi-company support

**Planned:**
- 🔄 Enhanced logging system
- 🔄 Automated tests
- 🔄 Docker containerization
- 🔄 Cloud deployment
- 🔄 AI-powered job parsing
- 🔄 Multi-user support

## Contributing

This is a personal project, but suggestions and improvements are welcome via issues.

## License

MIT

---

**Need help?** Check `CLAUDE.md` for development guidelines or `docs/ai/` for detailed specifications.
