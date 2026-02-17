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
│   ├── config.py                  # Settings from config.yaml
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
├── requirements.txt
└── config.yaml.example
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

### 3. Configure

Copy the example config and fill in your values:

```bash
cp config.yaml.example config.yaml
```

Edit `config.yaml`:

```yaml
telegram_bot_token: YOUR_BOT_TOKEN_HERE
telegram_chat_id: YOUR_CHAT_ID_HERE
scrape_interval: 60

vacancies:
  - name: "Uklon"
    url: "https://careers.uklon.net/vacancies-ua"
    keywords: ["middle", "data"]
  - name: "CD PROJEKT RED"
    url: "https://www.cdprojektred.com/en/jobs?studio=poland"
    keywords: ["developer"]
```

> **Note:** `config.yaml` is in `.gitignore` — it contains secrets and is never committed.

### 4. Get Telegram Credentials

### 5. Run

```bash
python main.py
```

The app will immediately run a scraping cycle, then repeat on the configured interval (default: 60 minutes). Press `Ctrl+C` to stop.

## Configuration Reference (`config.yaml`)

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `telegram_bot_token` | Yes | — | Telegram bot token from @BotFather |
| `telegram_chat_id` | Yes | — | Your Telegram chat/user ID |
| `scrape_interval` | No | `60` | Minutes between scraping cycles |
| `environment` | No | `development` | Logging level (`development` = DEBUG) |
| `vacancies` | Yes | — | List of companies to scrape |
| `vacancies[].name` | Yes | — | Must match a known scraper (see below) |
| `vacancies[].url` | Yes | — | Career page URL |
| `vacancies[].keywords` | Yes | — | Keywords to match jobs against (case-insensitive) |

## Dependencies

```
beautifulsoup4==4.12.3
requests==2.31.0
selenium==4.17.2
python-telegram-bot==21.0.1
apscheduler==3.10.4
pyyaml==6.0.2
webdriver-manager==4.0.1
```

## How Deduplication Works

Seen job URLs are kept in memory (`set`). On first run every job is new. On subsequent runs only jobs with previously unseen URLs trigger a notification. Restarting the app resets the seen-URLs set.

## Adding a New Company

1. Create `src/careers_scraper/scrapers/implementations/mycompany.py`:

```python
from careers_scraper.scrapers.base import BaseScraper

class MyCompanyScraper(BaseScraper):
    def __init__(self, url: str = "https://careers.mycompany.com"):
        super().__init__("MyCompany", url)

    def scrape(self) -> list[dict]:
        # return list of {"title", "url", "location", "department", "description"}
        return []
```

2. Add to `src/careers_scraper/scrapers/__init__.py` exports.
3. Register in `SCRAPER_REGISTRY` in `src/careers_scraper/services/scraper_service.py`:
   ```python
   "mycompany": MyCompanyScraper,
   ```
4. Add an entry to `config.yaml`:
   ```yaml
   - name: "MyCompany"
     url: "https://careers.mycompany.com"
     keywords: ["python", "backend"]
   ```

## Troubleshooting

**ChromeDriver not found** — Chrome must be installed. `webdriver-manager` downloads the correct ChromeDriver automatically.

**Telegram not sending** — Check that `telegram_bot_token` and `telegram_chat_id` are set in `config.yaml`, and that you've started a conversation with the bot.

**No jobs found** — Some scrapers (e.g. Uklon) have placeholder selectors. Run `python test_scraper.py uklon` to debug.

## License

MIT
