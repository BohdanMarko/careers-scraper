# Phase 1: Foundation

Restructure the codebase and add essential tooling. No new features -- only infrastructure.

---

## Scope

- Restructure project into `src/careers_scraper/` package layout
- Replace all `print()` with Python `logging`
- Refactor `config.py` with Pydantic `BaseSettings`, `env_prefix`
- Set up Alembic migrations (initial migration from current models)
- Create `pyproject.toml` (replace `requirements.txt`)
- Set up pytest with fixtures
- Extract embedded HTML/CSS/JS from `web_app.py` into static files
- Create repository pattern (`db/repositories/`)

## Non-Goals

- No new scrapers or scraper fixes (Phase 2)
- No Docker or deployment (Phase 3)
- No authentication (Phase 3)
- No cloud infrastructure (Phase 4)
- No new features

---

## Technical Design

### 1. Project Restructure

Move all source files from flat root into `src/careers_scraper/` package. Update all imports accordingly.

**Files to move:**

| Current Location | New Location |
|-----------------|-------------|
| `main.py` | `src/careers_scraper/main.py` |
| `config.py` | `src/careers_scraper/config.py` |
| `database.py` | Split into `src/careers_scraper/db/engine.py`, `session.py`, `models.py` |
| `scraper_service.py` | `src/careers_scraper/services/scraper_service.py` |
| `scrapers/base_scraper.py` | `src/careers_scraper/scrapers/base.py` |
| `scrapers/uklon_scraper.py` | `src/careers_scraper/scrapers/implementations/uklon.py` |
| `scrapers/cdprojektred_scraper.py` | `src/careers_scraper/scrapers/implementations/cdprojektred.py` |
| `scrapers/growe_scraper.py` | `src/careers_scraper/scrapers/implementations/growe.py` |
| `telegram_notifier.py` | `src/careers_scraper/notifications/telegram.py` |
| `web_app.py` | `src/careers_scraper/web/app.py` |

### 2. Configuration Refactor

```python
# src/careers_scraper/config.py
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAREERS_", env_file=".env")

    environment: str = "development"
    debug: bool = False
    database_url: str = "sqlite:///./careers.db"
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    search_keywords: str = "python,backend,developer"
    scrape_interval_minutes: int = 60

    @property
    def engine_kwargs(self) -> dict:
        if "sqlite" in self.database_url:
            return {"connect_args": {"check_same_thread": False}}
        return {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
```

### 3. Database Split

Split `database.py` into:

- **`db/engine.py`**: Engine factory using `Settings.database_url` and `Settings.engine_kwargs`
- **`db/session.py`**: `SessionLocal`, `get_db()` dependency
- **`db/models.py`**: SQLAlchemy ORM models (unchanged from current)
- **`db/repositories/job_repository.py`**: `JobRepository` with `upsert_batch()`, `get_jobs(offset, limit)`, `get_by_url()`
- **`db/repositories/company_repository.py`**: `CompanyRepository` with `get_active()`, `get_all()`

### 4. Logging Setup

```python
# src/careers_scraper/core/logging.py
import logging
import sys

def setup_logging(environment: str = "development"):
    level = logging.DEBUG if environment == "development" else logging.INFO
    fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    logging.basicConfig(level=level, format=fmt, stream=sys.stdout)
    # Suppress noisy libraries
    logging.getLogger("selenium").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("apscheduler").setLevel(logging.WARNING)
```

Every module uses: `logger = logging.getLogger(__name__)`

### 5. Alembic Setup

- Initialize Alembic in project root (`alembic/`, `alembic.ini`)
- Configure `alembic/env.py` to import models and use `Settings.database_url`
- Generate initial migration from existing models
- Remove `Base.metadata.create_all()` from startup; replace with `alembic upgrade head`

### 6. Static Files Extraction

Extract the ~100 lines of embedded HTML/CSS/JS from `web_app.py` into:
- `src/careers_scraper/web/static/index.html`
- `src/careers_scraper/web/static/style.css`
- `src/careers_scraper/web/static/app.js`

Mount static files via FastAPI's `StaticFiles`.

### 7. pyproject.toml

Replace `requirements.txt` with `pyproject.toml`:
- Build system: `setuptools`
- Dependencies: all current requirements.txt entries
- Optional deps: `[dev]` group with pytest, pytest-cov
- Entry point: `careers-scraper = "careers_scraper.main:main"`

### 8. Testing Setup

```
tests/
├── conftest.py              # In-memory SQLite session, TestClient fixture
├── unit/
│   ├── test_config.py       # Settings loading, defaults, env_prefix
│   └── test_repositories.py # CRUD operations on in-memory DB
└── integration/
    └── test_web_api.py      # FastAPI TestClient endpoint tests
```

---

## Data Model Changes

None. Models remain identical. The initial Alembic migration captures the current schema as-is.

---

## API Changes

None. All existing endpoints remain unchanged. The web dashboard serves the same content from static files instead of embedded strings.

---

## Files to Modify

| File | What Changes | Why |
|------|-------------|-----|
| `database.py` | Split into `db/engine.py`, `db/session.py`, `db/models.py`, `db/repositories/` | Foundation for repository pattern |
| `config.py` | Add `env_prefix`, new settings, Pydantic v2 `SettingsConfigDict` | Every module depends on this |
| `web_app.py` | Extract to `web/app.py` + static files | Maintainability |
| All source files | Replace `print()` with `logger.info/warning/error` | Structured logging |
| `main.py` | Update imports, call `setup_logging()` at startup | Lifecycle management |

---

## Implementation Checklist

- [ ] Create `src/careers_scraper/` directory structure with `__init__.py` files
- [ ] Move and refactor `config.py` with Pydantic `BaseSettings`
- [ ] Split `database.py` into `db/` modules
- [ ] Create `JobRepository` and `CompanyRepository`
- [ ] Create `core/logging.py` and replace all `print()` calls
- [ ] Extract HTML/CSS/JS from `web_app.py` into `web/static/`
- [ ] Move all source files to new package layout
- [ ] Update all imports across the codebase
- [ ] Initialize Alembic and create initial migration
- [ ] Create `pyproject.toml`
- [ ] Create `tests/conftest.py` with fixtures
- [ ] Write tests for config, repositories, and API endpoints
- [ ] Remove `requirements.txt` (replaced by `pyproject.toml`)

---

## Acceptance Criteria

1. `pytest` passes with all tests green
2. `alembic upgrade head` creates tables correctly on a fresh SQLite database
3. Web dashboard loads from static files (no embedded HTML in Python)
4. All `print()` statements replaced with `logging` calls
5. `from careers_scraper.config import Settings` works (package layout functional)
6. Repository classes handle CRUD with pagination
7. Application starts and runs identically to before restructuring

---

## Implementation Notes

- Keep the hard-coded scraper registry in `scraper_service.py` for now -- Phase 2 replaces it
- Keep the async/sync mismatch in Telegram notifier for now -- Phase 2 fixes it
- The Uklon scraper remains broken -- Phase 2 fixes it
- No new dependencies except `pydantic-settings` (if not already present) and `alembic`
