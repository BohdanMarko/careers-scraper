# CLAUDE.md

## Project Overview

**Project:** careers-scraper

A lightweight Python job scraping system with:
- Selenium-based scrapers for multiple company career pages
- Telegram notifications for keyword-matching jobs
- APScheduler for periodic scraping
- No database, no web server — scraping + notifications only

Current state: scraping + Telegram notifications only. No database, no web server.

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
python main.py

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
            └── TelegramNotifier.send_job_notification_sync()
```

### Module Boundaries

- Scrapers live in `src/careers_scraper/scrapers/implementations/`
- All scrapers inherit from `BaseScraper` in `scrapers/base.py`
- No business logic inside scrapers — they return `list[dict]` only
- Notification logic stays in `notifications/telegram.py`
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

# Run app
python main.py
```

---

## Configuration

All config lives in `config.yaml` (copy from `config.yaml.example`):

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
beautifulsoup4==4.12.3
requests==2.31.0
selenium==4.17.2
python-telegram-bot==21.0.1
apscheduler==3.10.4
pyyaml==6.0.2
webdriver-manager==4.0.1
```

No SQLAlchemy, no FastAPI, no Pydantic, no Alembic, no python-dotenv.

---

## Critical Files Reference

| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Root entry point wrapper | Imports from package |
| `src/careers_scraper/main.py` | App entry point | start scheduler → sleep loop |
| `src/careers_scraper/config.py` | Settings from config.yaml | PyYAML + dataclasses |
| `src/careers_scraper/scheduler.py` | APScheduler wrapper | Runs scraping cycle |
| `src/careers_scraper/services/scraper_service.py` | Orchestration | In-memory dedup, keyword match, notify |
| `src/careers_scraper/scrapers/base.py` | BaseScraper ABC | All scrapers inherit this |
| `src/careers_scraper/scrapers/implementations/uklon.py` | Uklon | **BROKEN** — placeholder selectors |
| `src/careers_scraper/scrapers/implementations/cdprojektred.py` | CD Projekt Red | Reads `window.cdpData.jobsData` |
| `src/careers_scraper/scrapers/implementations/growe.py` | Growe | Selenium, multi-selector fallback |
| `src/careers_scraper/notifications/telegram.py` | Telegram bot | HTML-formatted messages |
| `src/careers_scraper/core/logging.py` | Logging setup | Suppresses noisy libs |
| `test_scraper.py` | Manual testing | Not automated tests |

---

## Adding New Scrapers

1. Create `src/careers_scraper/scrapers/implementations/mycompany.py`
2. Inherit from `BaseScraper`, implement `scrape() -> list[dict]`, accept `url` param
3. Export from `src/careers_scraper/scrapers/__init__.py`
4. Add to `SCRAPER_REGISTRY` in `scraper_service.py`: `"mycompany": MyCompanyScraper`
5. Add entry to `config.yaml` under `vacancies`

---

## Current Known Issues

- **Uklon scraper broken** — placeholder CSS selectors, needs fixing

---

## Quick Reference Commands

```bash
.venv\Scripts\activate
python main.py
```

---

## Getting Help

- **README:** `README.md` — setup and usage
- **This File:** `CLAUDE.md` — development rules and architecture
