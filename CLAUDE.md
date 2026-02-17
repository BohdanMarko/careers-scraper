# CLAUDE.md

## Project Overview

**Project:** careers-scraper

A lightweight Python job scraping system with:
- Selenium-based scrapers for multiple company career pages
- Telegram notifications for keyword-matching jobs
- APScheduler for periodic scraping
- No database, no web server — scraping + notifications only

**Architecture & Roadmap:**

| Document | Purpose |
|----------|---------|
| `docs/ai/master-plan.md` | Vision, architecture, design decisions, roadmap overview |
| `docs/ai/phase-2-scrapers.spec.md` | Phase 2: Scraper Reliability (registry, browser, retry, fixes) |
| `docs/ai/phase-3-dashboard.spec.md` | Phase 3: Web dashboard (if ever re-added) |
| `docs/ai/phase-4-cloud.spec.md` | Phase 4: Cloud Deployment |

Claude must always align with the approved master plan and active phase spec.

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
- All AI-generated documentation must go to: `docs/ai/`
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

# Test a single scraper manually
python test_scraper.py uklon
python test_scraper.py cdprojektred
python test_scraper.py growe
python test_scraper.py all
```

---

## Environment Variables

Required in `.env` (copy from `.env.example`):

```env
TELEGRAM_BOT_TOKEN=...
TELEGRAM_CHAT_ID=...
SEARCH_KEYWORDS=python,backend,developer,engineer
SCRAPE_INTERVAL=60
ENVIRONMENT=development
```

Note: `CAREERS_` prefix is **NOT** used — plain variable names.

---

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

No SQLAlchemy, no FastAPI, no Pydantic, no Alembic.

---

## Critical Files Reference

| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Root entry point wrapper | Imports from package |
| `src/careers_scraper/main.py` | App entry point | start scheduler → sleep loop |
| `src/careers_scraper/config.py` | Settings via python-dotenv | Plain `os.getenv()` |
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
2. Inherit from `BaseScraper`, implement `scrape() -> list[dict]`
3. Export from `src/careers_scraper/scrapers/__init__.py`
4. Add instance to `scrapers` list in `src/careers_scraper/services/scraper_service.py`

---

## Current Known Issues

- **Uklon scraper broken** — placeholder CSS selectors, needs fixing
- `test_scraper.py` imports from old flat-root structure — needs updating

---

## Quick Reference Commands

```bash
.venv\Scripts\activate
python main.py
python test_scraper.py all
```

---

## Getting Help

- **Master Plan:** `docs/ai/master-plan.md`
- **Phase Specs:** `docs/ai/phase-*.spec.md`
- **README:** `README.md`
- **This File:** `CLAUDE.md`
