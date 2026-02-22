# Careers Scraper

A lightweight Python scraper that monitors company career pages, filters jobs by keywords, and sends Telegram notifications for matching positions.

## What It Does

- Scrapes career pages of configured companies (scheduled externally via Azure CRON)
- Runs all scrapers in parallel for speed (~15s per cycle)
- Filters new job listings by keywords (per-company, case-insensitive)
- Sends a single Telegram message summarising all companies per cycle
- Deduplicates jobs in memory — no database needed

## Supported Companies

- [Uklon](https://careers.uklon.net/vacancies-ua)
- [CD Projekt Red](https://www.cdprojektred.com/en/jobs)
- [Growe](https://growe.com/career)

## Project Structure

```
careers-scraper/
├── main.py                        # Single entry point — runs one cycle and exits
├── src/
│   ├── config.py                  # Settings from config.yaml + env var overrides
│   ├── core/
│   │   └── logging.py             # Logging setup, suppresses noisy libs
│   ├── scrapers/
│   │   ├── base.py                # BaseScraper ABC + Chrome driver factory
│   │   └── implementations/
│   │       ├── uklon.py
│   │       ├── cdprojektred.py
│   │       └── growe.py
│   ├── services/
│   │   └── scraper_service.py     # Orchestrates scraping + dedup + notifications
│   └── notifications/
│       └── telegram.py            # Telegram bot (HTML messages via requests.post)
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD: build Docker image + deploy to Azure
├── requirements.txt
├── config.example.yaml
└── Dockerfile
```

## Local Setup

### Prerequisites

- **Python 3.13+**
- **Google Chrome** (Selenium auto-downloads the matching ChromeDriver)
- **Telegram bot token and chat ID** — see [Getting Telegram Credentials](#getting-telegram-credentials) below

### 1. Create and activate virtual environment

```bash
python -m venv .venv
.venv\Scripts\activate        # Windows CMD / PowerShell
source .venv/Scripts/activate # Git Bash
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Configure

```bash
cp config.example.yaml config.yaml
```

Edit `config.yaml` with your credentials and keywords:

```yaml
telegram_bot_token: YOUR_BOT_TOKEN_HERE
telegram_chat_id: YOUR_CHAT_ID_HERE

vacancies:
  - name: "Uklon"
    url: "https://careers.uklon.net/vacancies-ua"
    keywords: ["middle", "data"]
  - name: "CD PROJEKT RED"
    url: "https://www.cdprojektred.com/en/jobs?studio=poland"
    keywords: ["developer"]
```

> `config.yaml` is in `.gitignore` — it contains secrets and is never committed.

### 4. Run

```bash
python main.py
```

Runs one scraping cycle and exits. Scheduling is handled externally (Azure CRON job in production, or a task scheduler locally).

---

## Getting Telegram Credentials

1. Open Telegram and message **@BotFather** → `/newbot` → follow prompts → copy the token
2. Add your bot to the target chat or channel
3. Send any message to that chat, then open:
   `https://api.telegram.org/bot<YOUR_TOKEN>/getUpdates`
4. Find `"chat":{"id": -123456789}` — that number is your chat ID

---

## Configuration Reference

| Field | Required | Default | Description |
|-------|----------|---------|-------------|
| `telegram_bot_token` | Yes | — | Bot token from @BotFather. Can also be set via `TELEGRAM_BOT_TOKEN` env var |
| `telegram_chat_id` | Yes | — | Target chat/channel ID. Can also be set via `TELEGRAM_CHAT_ID` env var |
| `environment` | No | `development` | `development` = DEBUG logging, `production` = INFO |
| `dedup_seen_urls` | No | `true` | Skip already-notified job URLs. Set to `false` in containers (no state between runs) |
| `vacancies` | Yes | — | List of companies to scrape, in the order they appear in Telegram messages |
| `vacancies[].name` | Yes | — | Must match a key in `SCRAPER_REGISTRY` (case-insensitive) |
| `vacancies[].url` | Yes | — | Career page URL passed to the scraper |
| `vacancies[].keywords` | Yes | — | Keywords matched against job title, department, and description |
| `log_rotation.max_bytes` | No | `10485760` | Max log file size before rotation (10 MB) |
| `log_rotation.backup_count` | No | `5` | Number of rotated log files to keep |

### Environment variable overrides

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables take precedence over `config.yaml` values. This is how secrets are injected in the Azure deployment without baking them into the image.

---

## How Deduplication Works

Seen job URLs are tracked in memory (`set`). On the first run every job is considered new. On subsequent runs only jobs with unseen URLs trigger a notification. Restarting the app resets the set.

Set `dedup_seen_urls: false` when running in containers — each container run is a fresh process with no state from previous runs, so deduplication is unnecessary.

---

## Adding a New Company

1. Create `src/scrapers/implementations/mycompany.py`:

```python
from scrapers.base import BaseScraper, create_chrome_driver
from selenium.webdriver.common.by import By

class MyCompanyScraper(BaseScraper):
    def __init__(self, url: str = "https://careers.mycompany.com"):
        super().__init__("MyCompany", url)

    def scrape(self) -> list[dict]:
        driver = None
        try:
            driver = create_chrome_driver()
            driver.get(self.url)
            # ... parse jobs ...
            return []
        except Exception as e:
            logger.error("Error scraping MyCompany: %s", e)
            return []
        finally:
            if driver:
                driver.quit()
```

2. Register in `SCRAPER_REGISTRY` in `src/services/scraper_service.py`:
```python
"mycompany": MyCompanyScraper,
```

3. Add an entry to `config.yaml`:
```yaml
- name: "MyCompany"
  url: "https://careers.mycompany.com"
  keywords: ["python", "backend"]
```

Each scraper must return a list of dicts with these keys:

| Key | Type | Description |
|-----|------|-------------|
| `title` | `str` | Job title |
| `url` | `str` | Job detail URL — used for deduplication, must be unique per job |
| `location` | `str` | Office location |
| `department` | `str` | Team or department |
| `description` | `str` | Any extra text to match keywords against |
| `posted_date` | `datetime \| None` | Posting date if available |

---

## Deployment

The app is designed to run as an **Azure Container Apps Job** on a CRON schedule (every 60 minutes). Each run spins up a fresh container, runs one scraping cycle, sends notifications, and exits. No infrastructure runs between cycles — cost is effectively $0/month.

The `.github/workflows/deploy.yml` workflow automatically builds and pushes a new Docker image to ghcr.io and updates the Azure job on every push to `master`.

---

## Dependencies

```
requests==2.31.0
selenium==4.17.2
pyyaml==6.0.2
```

No database, no web server, no ORM, no SDK wrappers.

---

## Troubleshooting

**No jobs found** — Keywords must appear in the job title, department, or description. Check spelling and try broader terms.

**Telegram not sending** — Verify `telegram_bot_token` and `telegram_chat_id` in `config.yaml`. Make sure you've sent at least one message to the bot first.

**ChromeDriver error** — Selenium 4.6+ auto-downloads the matching ChromeDriver. If it fails, set the `CHROMEDRIVER_PATH` env var to the driver binary path, and `CHROME_BINARY` to the Chrome binary path.

**Scraper returns 0 jobs** — The career page HTML may have changed. Check the CSS selectors in the scraper implementation against the current live page.

