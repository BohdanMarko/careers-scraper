# Careers Scraper

A Python-based web scraper that monitors career pages of different companies, filters jobs by keywords, and sends Telegram notifications for matching positions.

## Features

- 🔍 Scrapes multiple company career pages, each page can have different HTML structure, etc, so it is needed to have different approach for each careers page, or use AI for parsing (find existing solutions). Here is the list of initial careers pages (it shoild be agile for extension in the future, the process of adding new careers pages should be simplided for the end user):
    - https://careers.uklon.net/vacancies-ua
    - https://www.cdprojektred.com/en/jobs?studio=poland#studio-operations
    - https://www.cdprojektred.com/en/jobs?studio=poland
    - https://growe.com/career

- 🎯 Filters jobs by customizable keywords or phrases
- 📱 Telegram notifications for matching positions (needed a telegram bot and valid telegram API)
- 🌐 Real-time web dashboard to view all jobs - it must be beautifully designed and be adaptive
- ⏰ Automated hourly checks - must be available to configure time for checks via some configuration
- 💾 SQLite database for job storage - locally SQLite should be good, but what about cloud?

- It should be ready for cloud deployment - firstly, I want to try it on Azure, then we will try AWS

TELEGRAM BOT:
- https://t.me/CareersScraperBot
- HTTP API KEY - {ask me to provide it}
- API DOCS https://core.telegram.org/bots/api

## Project Structure

```
careers-scraper/
├── main.py                 # Application entry point
├── config.py              # Configuration management
├── database.py            # Database models and setup
├── scraper_service.py     # Main scraping orchestration
├── scheduler.py           # Job scheduling
├── telegram_notifier.py   # Telegram bot integration
├── web_app.py            # FastAPI web interface
├── scrapers/
│   ├── __init__.py
│   ├── base_scraper.py   # Base scraper class
│   └── uklon_scraper.py  # Uklon-specific scraper
├── requirements.txt       # Python dependencies
├── .env.example          # Environment variables template
└── README.md
```

## Setup

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Configure Environment

Copy `.env.example` to `.env` and fill in your details:

```bash
cp .env.example .env
```

Edit `.env`:
```
TELEGRAM_BOT_TOKEN=your_bot_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SEARCH_KEYWORDS=python,backend,developer,engineer
```

### 3. Get Telegram Bot Token

1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Create a new bot with `/newbot`
3. Copy the token to your `.env` file

### 4. Get Your Chat ID

1. Talk to [@userinfobot](https://t.me/userinfobot) on Telegram
2. Copy your Chat ID to your `.env` file

## Usage

### Run the Application

```bash
python main.py
```

This will:
- Initialize the database
- Start the scheduler (scrapes every 60 minutes)
- Launch the web dashboard at http://localhost:8000

### Web Dashboard

Open http://localhost:8000 in your browser to:
- View all scraped jobs
- Filter by keyword matches
- See real-time statistics
- Auto-refreshes every 30 seconds

## Adding New Career Pages

To add a new company:

1. Create a new scraper in `scrapers/` (inherit from `BaseScraper`)
2. Implement the `scrape()` method
3. Register it in `scraper_service.py`
4. Add the company to the database

Example:
```python
# scrapers/mycompany_scraper.py
from .base_scraper import BaseScraper

class MyCompanyScraper(BaseScraper):
    def __init__(self):
        super().__init__("MyCompany", "https://careers.mycompany.com")

    def scrape(self):
        # Implement scraping logic
        return jobs
```

## Customization

### Change Scraping Interval

Edit `.env`:
```
SCRAPE_INTERVAL=120  # Minutes
```

### Add Keywords

Edit `.env`:
```
SEARCH_KEYWORDS=python,django,fastapi,react,typescript
```

## Notes

- The Uklon scraper uses Selenium for dynamic content (JavaScript-rendered pages)
- Chrome/Chromium must be installed for Selenium to work
- First run will take longer as ChromeDriver is downloaded
- The database is SQLite by default (stored as `careers.db`)

## Next Steps

1. Inspect the actual Uklon careers page and update CSS selectors in `uklon_scraper.py`
2. Add more company scrapers
3. Test Telegram notifications
4. Customize keyword matching logic
5. Add more features (email notifications, job descriptions, etc.)

## License

MIT
