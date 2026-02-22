# CLAUDE.md

## Project Overview

**Project:** careers-scraper

A lightweight Python job scraping system with:
- Selenium-based scrapers for multiple company career pages
- Telegram notifications for keyword-matching jobs
- Scheduling handled externally by Azure CRON — not inside the app
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

# Run application (one cycle, then exits)
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
Azure CRON (every 60 min)
    └── Container spins up → python main.py
            └── ScraperService.run_scraping_cycle()
                    ├── UklonScraper.scrape()        ─┐
                    ├── CDProjektRedScraper.scrape()  ├─ parallel (ThreadPoolExecutor)
                    └── GroweScraper.scrape()        ─┘
                            ↓ new URLs only (in-memory dedup)
                    └── keyword match?
                            ↓ yes
                    └── TelegramNotifier.send_cycle_summary()
            └── Container exits
```

### Module Boundaries

- Scrapers live in `src/scrapers/implementations/`
- All scrapers inherit from `BaseScraper` in `src/scrapers/base.py`
- No business logic inside scrapers — they return `list[dict]` only
- Notification logic stays in `src/notifications/telegram.py`
- No DB, no web server, no scheduler inside the app

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

# Run one scraping cycle and exit
python main.py
```

---

## Configuration

All config lives in `config.yaml` (copy from `config.example.yaml`):

```yaml
telegram_bot_token: ...
telegram_chat_id: ...
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

`TELEGRAM_BOT_TOKEN` and `TELEGRAM_CHAT_ID` environment variables override config.yaml values (used in Azure deployment).

Keywords are **per-vacancy**, not global.

---

## Dependencies

```
requests==2.31.0
selenium==4.17.2
pyyaml==6.0.2
```

No APScheduler, no SQLAlchemy, no FastAPI, no Pydantic, no Alembic, no python-dotenv, no webdriver-manager.
Telegram notifications use `requests.post()` directly (no telegram bot SDK).

---

## Project Structure

```
careers-scraper/
├── main.py                        # Entry point — runs one cycle and exits
├── src/
│   ├── config.py                  # Settings from config.yaml (PyYAML + dataclasses)
│   ├── core/
│   │   └── logging.py             # Logging setup, suppresses noisy libs
│   ├── scrapers/
│   │   ├── base.py                # BaseScraper ABC + create_chrome_driver()
│   │   └── implementations/
│   │       ├── uklon.py
│   │       ├── cdprojektred.py
│   │       └── growe.py
│   ├── services/
│   │   └── scraper_service.py     # Orchestration: parallel scraping, dedup, notify
│   └── notifications/
│       └── telegram.py            # Telegram bot (requests.post, HTML format)
├── .github/
│   └── workflows/
│       └── deploy.yml             # CI/CD: build + push Docker image + update Azure job
├── Dockerfile
├── requirements.txt
└── config.example.yaml
```

## Critical Files Reference

| File | Purpose | Notes |
|------|---------|-------|
| `main.py` | Entry point | Runs one scraping cycle and exits |
| `src/config.py` | Settings from config.yaml | PyYAML + dataclasses, env var overrides |
| `src/services/scraper_service.py` | Orchestration | Parallel scraping, in-memory dedup, keyword match, notify |
| `src/scrapers/base.py` | BaseScraper ABC | All scrapers inherit this; `create_chrome_driver()` lives here |
| `src/scrapers/implementations/uklon.py` | Uklon scraper | Selenium, CSS selectors, WebDriverWait |
| `src/scrapers/implementations/cdprojektred.py` | CD Projekt Red | Reads `window.cdpData.jobsData` via JS execution |
| `src/scrapers/implementations/growe.py` | Growe | Selenium, clicks VIEW MORE until all jobs loaded |
| `src/notifications/telegram.py` | Telegram bot | HTML messages via requests.post, retry logic |
| `src/core/logging.py` | Logging setup | Suppresses noisy libs |

---

## Adding New Scrapers

1. Create `src/scrapers/implementations/mycompany.py`
2. Inherit from `BaseScraper`, implement `scrape() -> list[dict]`, use `create_chrome_driver()`
3. Add to `SCRAPER_REGISTRY` in `src/services/scraper_service.py`: `"mycompany": MyCompanyScraper`
4. Add entry to `config.yaml` under `vacancies` — name must match the registry key (case-insensitive)

---

## Quick Reference Commands

```bash
source .venv/Scripts/activate
python main.py
```

---

## Getting Help

- **README:** `README.md` — setup and usage
- **This File:** `CLAUDE.md` — development rules and architecture
