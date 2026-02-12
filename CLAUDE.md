# CLAUDE.md

## Project Overview

**Project:** careers-scraper

A modular Python job scraping system with:
- Extensible scraper architecture (decorator-based registry)
- Telegram notifications for matching jobs
- FastAPI web dashboard
- SQLite (local) / PostgreSQL (cloud)
- Azure-first cloud deployment strategy

**Master architecture plan:** `docs/ai/master-plan.md`

Claude must always align with the approved master plan.

---

## 🚨 CRITICAL: Python Environment

**ALWAYS run or debug applications locally in the active `.venv`**

- Never use global Python interpreter
- Always activate `.venv` before running any Python commands
- Commands must be run from project root: `D:\Projects\careers-scraper`
- Verify venv is active: `python --version` should show Python 3.12.x

```bash
# Activate venv (Windows)
.venv\Scripts\activate

# Run application
python main.py

# Run tests
pytest

# Install dependencies
pip install -r requirements.txt
```

---

## General Rules

- **NEVER auto-commit changes** - only prepare commits when explicitly asked via `/commit`
- **NEVER create files outside the project structure** unless explicitly asked
- All AI-generated documentation must go to: `docs/ai/`
- Temporary debug scripts must go into: `tools/`
- Do not refactor unrelated modules without explicit request
- Do not introduce new dependencies without justification and alignment with master-plan.md
- Do not change architecture without referencing `docs/ai/master-plan.md`
- Always check if files exist before creating them

---

## Development Guidelines

### Code Organization
- Follow modular design as defined in master-plan.md
- Future structure: `src/careers_scraper/` package layout (Phase 1)
- Current structure: flat root directory with `scrapers/` subdirectory

### Module Boundaries
- Scrapers must inherit from `BaseScraper` (in `scrapers/base_scraper.py`)
- No business logic inside `web_app.py` - keep it thin
- No Telegram logic outside `telegram_notifier.py`
- Database access should go through repositories (future: Phase 1)
- No hardcoded secrets - never commit `.env`
- Always use environment variables via `config.py`

### Scraper Registry (Future - Phase 2)
- Use `@register_scraper("company_name")` decorator
- Auto-discovery via `pkgutil.iter_modules()`
- No manual registry updates in `scraper_service.py`

---

## Build & Run

### Local Development

```bash
# Activate virtual environment (REQUIRED)
.venv\Scripts\activate

# Run application
python main.py

# Run a specific scraper test
python test_scraper.py uklon
python test_scraper.py cdprojektred
python test_scraper.py growe
python test_scraper.py all
```

### Web Dashboard
- URL: http://localhost:8000
- No authentication (dev mode)
- Auto-refreshes every 30 seconds

### Environment Variables

Required in `.env`:
```
TELEGRAM_BOT_TOKEN=your_token_here
TELEGRAM_CHAT_ID=your_chat_id_here
SEARCH_KEYWORDS=python,backend,developer,engineer
DATABASE_URL=sqlite:///./careers.db
WEB_HOST=0.0.0.0
WEB_PORT=8000
SCRAPE_INTERVAL=60
```

---

## Testing

### Manual Testing
```bash
# Test individual scrapers
python test_scraper.py uklon
python test_scraper.py cdprojektred
python test_scraper.py growe
```

### Automated Testing (Future - Phase 1)
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src/careers_scraper
```

---

## Logs & Debugging

**Current:** All output via `print()` statements (to be replaced in Phase 1)

**Future (Phase 1):**
- All logs must go into: `logs/`
- Use structured logging via `core/logging.py`
- Human-readable format in dev, JSON in production
- Never spam print statements

**Logging levels:**
- `INFO`: Normal operations, scraping cycles, jobs found
- `WARNING`: Recoverable issues, missing selectors
- `ERROR`: Failures, network errors, scraper crashes
- `DEBUG`: Detailed tracing (dev only)

---

## Git Rules

- **NEVER run git add/commit automatically** under any circumstances
- Only prepare commit messages when explicitly asked via `/commit` skill
- Assume code is uncommitted unless user confirms
- Always check `git status` before making suggestions about commits
- Never use `--no-verify` or skip pre-commit hooks
- Never force push to main/master

---

## Current Project Phase

**Phase:** Pre-Phase 1 (Prototype)

**Current State:**
- Functional prototype with 3 scrapers (Uklon, CD Projekt Red, Growe)
- Hard-coded scraper registry in `scraper_service.py`
- Embedded HTML/CSS/JS in `web_app.py`
- No logging framework (all `print()`)
- No database migrations (Alembic)
- No automated tests
- Uklon scraper has placeholder selectors (broken)

**Next Phase:** Phase 1 - Foundation
- Restructure to `src/careers_scraper/` layout
- Replace `print()` with logging
- Set up Alembic migrations
- Create `pyproject.toml`
- Extract web dashboard to static files
- Implement repository pattern
- Set up pytest

---

## Cloud Goals

**Target Deployment:**
- **Hosting:** Azure Container Apps (consumption-based pricing)
- **Database:** Azure Database for PostgreSQL Flexible Server (B1ms tier)
- **Secrets:** Azure Key Vault with managed identity
- **Registry:** Azure Container Registry (Basic tier)
- **Monitoring:** Azure Application Insights (Phase 4)

**Estimated Cost:** ~$23-33/month

**Future:** AWS compatibility (ECS Fargate + RDS PostgreSQL)

**Deployment Approach:**
- Docker-first deployment
- Environment-based configuration
- Prioritize cloud portability
- Single container runs web + scheduler

---

## Architecture Principles

### Simplicity First
- Single-process monolith (web + scheduler in one container)
- No microservices unless strongly justified
- No message queues for a solo developer at this scale
- APScheduler (not Celery) for background jobs

### Design Patterns to Follow
- **Strategy:** `BaseScraper` ABC with implementations
- **Registry/Factory:** `@register_scraper` decorator pattern
- **Repository:** Data access abstraction (Phase 1)
- **Context Manager:** Shared browser lifecycle
- **Observer:** Notification channels (Telegram, future: email)

### What NOT to Add
- Don't add Celery (overkill for hourly scraping)
- Don't split into microservices
- Don't add Redis/RabbitMQ
- Don't create abstractions until needed
- Don't add features beyond current phase scope

---

## Scope Discipline

**Before implementing any task:**
1. Check which phase it belongs to in `docs/ai/master-plan.md`
2. If outside current phase: **Ask for clarification** before proceeding
3. Never expand scope autonomously
4. Always reference the master plan when suggesting architectural changes

**When in doubt:**
- Prefer simpler solutions
- Prioritize getting current phase working over future optimization
- Ask clarifying questions rather than making assumptions

---

## Adding New Scrapers

### Current Process (Pre-Phase 2)
1. Create new file in `scrapers/` (e.g., `mycompany_scraper.py`)
2. Inherit from `BaseScraper`
3. Implement `scrape()` method
4. Update `scrapers/__init__.py` exports
5. Add to registry dict in `scraper_service.py` lines 15-19
6. Add company row to database via manual script or dashboard

### Future Process (Phase 2+)
1. Create new file in `src/careers_scraper/scrapers/implementations/`
2. Decorate with `@register_scraper("company name")`
3. Add company row to database
4. **That's it** - auto-discovery handles the rest

---

## Critical Files Reference

| File | Purpose | Current Issues |
|------|---------|---------------|
| `main.py` | Entry point, lifecycle | Needs graceful shutdown |
| `config.py` | Settings management | Needs `env_prefix`, validators |
| `database.py` | ORM models | Needs split into engine/session/models/repos |
| `scraper_service.py` | Orchestration | Hard-coded registry, no retry logic |
| `scrapers/base_scraper.py` | Scraper ABC | Needs `ScrapeMethod` enum |
| `scrapers/uklon_scraper.py` | Uklon scraper | **BROKEN** - placeholder selectors |
| `telegram_notifier.py` | Notifications | Async/sync mismatch, no HTML escaping |
| `web_app.py` | FastAPI dashboard | Embedded HTML, no auth, no pagination |
| `test_scraper.py` | Manual testing | Not automated tests |

---

## Quick Reference Commands

```bash
# Environment
.venv\Scripts\activate

# Run app
python main.py

# Test scrapers
python test_scraper.py all

# Future: Tests
pytest

# Future: Migrations
alembic upgrade head
alembic revision --autogenerate -m "description"

# Future: Docker
docker-compose up
docker build -t careers-scraper .
```

---

## Getting Help

- **Master Plan:** `docs/ai/master-plan.md` - comprehensive architecture guide
- **README:** `README.md` - project overview and setup
- **This File:** `CLAUDE.md` - development rules and quick reference
