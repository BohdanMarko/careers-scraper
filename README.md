# Careers Scraper

A lightweight Python scraper that monitors company career pages, filters jobs by keywords, and sends Telegram notifications for matching positions.

## What It Does

- Scrapes career pages of configured companies on a fixed schedule
- Filters new job listings by keywords
- Sends a Telegram message for every new matching job
- Deduplicates jobs in memory (no database needed)

## Supported Companies

- [Uklon](https://careers.uklon.net/vacancies-ua)
- [CD Projekt Red](https://www.cdprojektred.com/en/jobs)
- [Growe](https://growe.com/career)

## Project Structure

```
careers-scraper/
├── src/careers_scraper/
│   ├── config.py                  # Settings from .env
│   ├── main.py                    # Entry point
│   ├── scheduler.py               # APScheduler wrapper
│   ├── core/
│   │   └── logging.py            # Logging setup
│   ├── scrapers/
│   │   ├── base.py               # BaseScraper ABC
│   │   └── implementations/
│   │       ├── uklon.py
│   │       ├── cdprojektred.py
│   │       └── growe.py
│   ├── services/
│   │   └── scraper_service.py    # Orchestrates scraping + notifications
│   └── notifications/
│       └── telegram.py           # Telegram bot
├── main.py                        # Entry point wrapper
├── test_scraper.py               # Manual scraper test tool
├── requirements.txt
└── .env.example
```

## Local Setup

### Prerequisites

- **Python 3.12+** (Windows official build recommended, not msys64)
- **Google Chrome** (for Selenium-based scrapers)
- **Telegram Bot token and chat ID**

### 1. Create and Activate Virtual Environment

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows CMD / PowerShell
source .venv/Scripts/activate # Git Bash
```

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
```

Edit `.env`:

```env
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SEARCH_KEYWORDS=python,backend,developer,engineer
SCRAPE_INTERVAL=60
```

### 4. Get Telegram Credentials

**Bot token:**
1. Talk to [@BotFather](https://t.me/botfather) on Telegram
2. Send `/newbot`, follow the prompts
3. Copy the token into `TELEGRAM_BOT_TOKEN`

**Chat ID:**
1. Talk to [@userinfobot](https://t.me/userinfobot)
2. Copy the ID into `TELEGRAM_CHAT_ID`

### 5. Run

```bash
python main.py
```

The app will immediately run a scraping cycle, then repeat on the configured interval (default: 60 minutes). Press `Ctrl+C` to stop.

## Testing Individual Scrapers

```bash
python test_scraper.py uklon
python test_scraper.py cdprojektred
python test_scraper.py growe
python test_scraper.py all
```

## Dependencies

```
beautifulsoup4==4.12.3
requests==2.31.0
selenium==4.17.2
python-telegram-bot==21.0.1
apscheduler==3.10.4
python-dotenv==1.0.1
webdriver-manager==4.0.1
```

## How Deduplication Works

Seen job URLs are kept in memory (`set`). On first run every job is new. On subsequent runs only jobs with previously unseen URLs trigger a notification. Restarting the app resets the seen-URLs set.

## Adding a New Company

1. Create `src/careers_scraper/scrapers/implementations/mycompany.py`:

```python
from careers_scraper.scrapers.base import BaseScraper

class MyCompanyScraper(BaseScraper):
    def __init__(self):
        super().__init__("MyCompany", "https://careers.mycompany.com")

    def scrape(self) -> list[dict]:
        # return list of {"title", "url", "location", "department", "description"}
        return []
```

2. Add to `src/careers_scraper/scrapers/__init__.py` exports.
3. Add an instance to the `scrapers` list in `src/careers_scraper/services/scraper_service.py`.

## Troubleshooting

**ChromeDriver not found** — Chrome must be installed. `webdriver-manager` downloads the correct ChromeDriver automatically.

**Telegram not sending** — Check that `TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` are set, and that you've started a conversation with the bot.

**No jobs found** — Some scrapers (e.g. Uklon) have placeholder selectors. Run `python test_scraper.py uklon` to debug.

## License

MIT
