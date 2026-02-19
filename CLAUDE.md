# CLAUDE.md

## Project Overview

**Project:** careers-scraper

A lightweight Python job scraping system with:
- Selenium-based scrapers for multiple company career pages
- Telegram notifications for keyword-matching jobs
- APScheduler for periodic scraping
- No database, no web server — scraping + notifications only

---

## 🚨 CRITICAL: Python Environment

**ALWAYS use the active `.venv` (Windows Python 3.13)**

- Never use global Python interpreter
- Commands must be run from project root: `D:\Projects\careers-scraper`
- Venv uses Windows Python 3.13 at `.venv\Scripts\python.exe`

```bash
# Activate venv
.venv\Scripts\activate         # Windows CMD / PowerShell
source .venv/Scripts/activate  # Git Bash

# Run application
python main.py                 # scheduler mode (default)
python main.py --single-run    # run once and exit

# Install dependencies
pip install -r requirements.txt
```

---

## General Rules

- **NEVER auto-commit changes** - only prepare commits when explicitly asked via `/commit`
- **NEVER create files outside the project structure** unless explicitly asked
- Do not refactor unrelated modules without explicit request
- Do not introduce new dependencies without justification
- Always check if files exist before creating them

---

## Development Guidelines

### What This App Does

```
Scheduler (APScheduler)
    └── ScraperService.run_scraping_cycle()
            ├── UklonScraper.scrape()        → list[dict]
            ├── CDProjektRedScraper.scrape() → list[dict]
            └── GroweScraper.scrape()        → list[dict]
                    ↓ new URLs only (in-memory dedup)
            └── keyword match?
                    ↓ yes
            └── TelegramNotifier.send_company_jobs()
```

### Module Boundaries

- Scrapers live in `src/scrapers/implementations/`
- All scrapers inherit from `BaseScraper` in `src/scrapers/base.py`
- No business logic inside scrapers — they return `list[dict]` only
- Notification logic stays in `src/notifications/telegram.py`
- No DB, no web server

### Job Dict Format (returned by scrapers)

```python
{
    "title":       str,
    "url":         str,   # used for deduplication — must be unique per job
    "location":    str,
    "department":  str,
    "description": str,
    "posted_date": datetime | None,
}
```

---

## Build & Run

```bash
# Activate venv
.venv\Scripts\activate

# Run scheduler (periodic scraping, Ctrl+C to stop)
python main.py

# Run one cycle and exit
python main.py --single-run
```

---

## Configuration

All config lives in `config.yaml` (copy from `config.example.yaml`):

```yaml
telegram_bot_token: ...
telegram_chat_id: ...
scrape_interval: 60
environment: development

vacancies:
  - name: "Uklon"
    url: "https://careers.uklon.net/vacancies-ua"
    keywords: ["middle", "data"]
  - name: "CD PROJEKT RED"
    url: "https://www.cdprojektred.com/en/jobs?studio=poland"
    keywords: ["developer"]
```

**`config.yaml` is in `.gitignore` — contains secrets, never commit it.**

Keywords are **per-vacancy**, not global.

---

## Dependencies

```
requests==2.31.0
selenium==4.17.2
apscheduler==3.10.4
pyyaml==6.0.2
```

No SQLAlchemy, no FastAPI, no Pydantic, no Alembic, no python-dotenv, no webdriver-manager.
Telegram notifications use `requests.post()` directly (no telegram bot SDK).

---

## Project Structure

```
careers-scraper/
├── main.py                        # Single entry point (--single-run flag)
├── src/
│   ├── config.py                  # Settings from config.yaml (PyYAML + dataclasses)
│   ├── scheduler.py               # APScheduler wrapper
│   ├── core/
│   │   └── logging.py             # Logging setup, suppresses noisy libs
│   ├── scrapers/
│   │   ├── base.py                # BaseScraper ABC
│   │   └── implementations/
│   │       ├── uklon.py
│   │       ├── cdprojektred.py
│   │       └── growe.py
│   ├── services/
│   │   └── scraper_service.py     # Orchestration: dedup, keyword match, notify
│   └── notifications/
│       └── telegram.py            # Telegram bot (requests.post, HTML format)
├── requirements.txt
└── config.example.yaml
```

## Critical Files Reference

| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Single entry point | `--single-run` flag to run once |
| `src/config.py` | Settings from config.yaml | PyYAML + dataclasses |
| `src/scheduler.py` | APScheduler wrapper | Runs scraping cycle on interval |
| `src/services/scraper_service.py` | Orchestration | In-memory dedup, keyword match, notify |
| `src/scrapers/base.py` | BaseScraper ABC | All scrapers inherit this |
| `src/scrapers/implementations/uklon.py` | Uklon scraper | Selenium, CSS selectors |
| `src/scrapers/implementations/cdprojektred.py` | CD Projekt Red | Reads `window.cdpData.jobsData` |
| `src/scrapers/implementations/growe.py` | Growe | Selenium, clicks VIEW MORE |
| `src/notifications/telegram.py` | Telegram bot | HTML messages via requests.post |
| `src/core/logging.py` | Logging setup | Suppresses noisy libs |

---

## Adding New Scrapers

1. Create `src/scrapers/implementations/mycompany.py`
2. Inherit from `BaseScraper`, implement `scrape() -> list[dict]`, accept `url` param
3. Export from `src/scrapers/__init__.py`
4. Add to `SCRAPER_REGISTRY` in `src/services/scraper_service.py`: `"mycompany": MyCompanyScraper`
5. Add entry to `config.yaml` under `vacancies`

---

## Quick Reference Commands

```bash
.venv\Scripts\activate
python main.py
python main.py --single-run
```

---

## Getting Help

- **README:** `README.md` — setup and usage
- **This File:** `CLAUDE.md` — development rules and architecture
