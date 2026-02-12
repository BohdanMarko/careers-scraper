# Careers Scraper: Architectural Review & Implementation Roadmap

---

## 1. Current State Assessment

### What Exists

A functional prototype (~550 lines Python, 12 source files) with the correct conceptual structure: FastAPI web dashboard, APScheduler background scraping, Selenium-based scrapers with an ABC base class, Telegram notifications, and SQLAlchemy/SQLite persistence. Three scrapers (Uklon, CD Projekt Red, Growe) are implemented.

### Critical Gaps (by severity)

**Broken functionality:**
- `uklon_scraper.py` uses placeholder CSS selectors (`[class*='vacancy']`, `[class*='job']`) - explicitly marked TODO, returns zero results on the real page
- `telegram_notifier.py` calls `asyncio.run()` per message inside `send_job_notification_sync()` - creates a new event loop each time, will crash if called from within an existing async context

**Security & reliability:**
- No authentication on the web dashboard - anyone with network access can view all data
- HTML injection in Telegram messages and web dashboard (job titles inserted without escaping)
- No retry logic anywhere - single network failure silently drops an entire company's scraping cycle
- All exceptions caught with bare `except Exception as e: print(...)` pattern

**Technical debt:**
- No logging framework - 25+ `print()` statements, no log levels, no persistence
- No database migrations - `Base.metadata.create_all()` only; schema changes require deleting the DB
- No automated tests (`test_scraper.py` is a manual CLI debug script requiring a live browser)
- No Docker or deployment configuration
- Hard-coded scraper registry in `scraper_service.py` lines 15-19 - adding scrapers requires code changes in 2 files
- Selenium used universally, including potentially for pages that could use `httpx` + BeautifulSoup
- `beautifulsoup4` and `requests` in requirements.txt but never imported
- 100+ lines of embedded HTML/CSS/JS in `web_app.py` as a Python string literal
- No pagination on `/api/jobs` - all jobs loaded into memory
- No health check endpoints, no graceful shutdown, no environment profiles

---

## 2. Target Architecture

### Project Structure

```
careers-scraper/
├── src/
│   └── careers_scraper/
│       ├── __init__.py
│       ├── main.py                      # Entry point, lifecycle management
│       ├── config.py                    # Pydantic settings with env_prefix
│       │
│       ├── core/
│       │   ├── __init__.py
│       │   ├── logging.py              # Structured logging setup
│       │   └── exceptions.py           # Custom exception hierarchy
│       │
│       ├── db/
│       │   ├── __init__.py
│       │   ├── engine.py              # Engine factory (SQLite/PostgreSQL)
│       │   ├── session.py             # Session management, get_db
│       │   ├── models.py             # SQLAlchemy ORM models
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── job_repository.py  # CRUD for Job with pagination
│       │       └── company_repository.py
│       │
│       ├── scrapers/
│       │   ├── __init__.py            # Auto-discovery via pkgutil
│       │   ├── base.py               # BaseScraper ABC + ScrapeMethod enum
│       │   ├── registry.py           # @register_scraper decorator + factory
│       │   ├── browser.py            # Shared Selenium context manager
│       │   ├── http_client.py        # httpx client for static scrapers
│       │   ├── ai_parser.py          # LLM fallback parser (Phase 5)
│       │   └── implementations/
│       │       ├── __init__.py
│       │       ├── uklon.py
│       │       ├── cdprojektred.py
│       │       └── growe.py
│       │
│       ├── notifications/
│       │   ├── __init__.py
│       │   ├── base.py               # NotificationChannel ABC
│       │   ├── telegram.py           # Telegram implementation
│       │   └── manager.py            # Dispatches to active channels
│       │
│       ├── services/
│       │   ├── __init__.py
│       │   └── scraper_service.py    # Orchestration: scrape -> dedupe -> notify
│       │
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── scheduler.py          # APScheduler wrapper with health tracking
│       │
│       └── web/
│           ├── __init__.py
│           ├── app.py                # FastAPI app factory
│           ├── auth.py               # API key auth middleware
│           ├── schemas.py            # Pydantic request/response models
│           ├── routes/
│           │   ├── __init__.py
│           │   ├── jobs.py           # /api/jobs with pagination
│           │   ├── companies.py      # /api/companies
│           │   ├── health.py         # /health, /ready
│           │   └── stats.py          # /api/stats
│           └── static/
│               ├── index.html
│               ├── style.css
│               └── app.js
│
├── alembic/
│   ├── env.py
│   └── versions/
│
├── tests/
│   ├── conftest.py                   # Fixtures: in-memory SQLite, TestClient
│   ├── unit/
│   │   ├── test_config.py
│   │   ├── test_repositories.py
│   │   ├── test_scraper_service.py
│   │   └── test_notifications.py
│   └── integration/
│       ├── test_web_api.py
│       └── test_scraper_registry.py
│
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── alembic.ini
├── .env.example
├── .gitignore
└── README.md
```

### Data Flow

```
[APScheduler tick] ──> [ScraperService.run_cycle()]
                              │
                              ├──> CompanyRepository.get_active() ──> list of companies
                              │
                              └──> for each company:
                                      │
                                      ├──> ScraperRegistry.get(name) ──> BaseScraper instance
                                      ├──> scraper.scrape() via browser.py or http_client.py
                                      ├──> JobRepository.upsert_batch(jobs) ──> dedupe by URL
                                      └──> NotificationManager.notify(new matching jobs)
                                              └──> TelegramChannel.send(job)
```

### Key Design Decisions

| Decision | Choice | Justification |
|----------|--------|---------------|
| Monolith vs microservices | **Single process monolith** | Solo developer; web + scheduler + scrapers in one process is simpler to develop, debug, and deploy. Internal packages provide separation of concerns. |
| APScheduler vs Celery | **APScheduler** | Celery requires Redis/RabbitMQ broker + separate worker. APScheduler runs in-process and handles "run every N minutes" without infrastructure overhead. |
| Selenium vs Playwright | **Keep Selenium (for now)** | Already works, all 3 scrapers use it. `browser.py` abstraction allows future Playwright migration with minimal impact. |
| In-process events vs message queue | **In-process NotificationManager** | One event type, 1-2 handlers. Redis pub/sub adds operational cost for zero benefit at this scale. |

---

## 3. Scraper Strategy

### When to Use What

| Technique | Use When | Cost |
|-----------|----------|------|
| `httpx` + BeautifulSoup | Content is in initial HTML (server-rendered) | Low - no browser |
| Selenium (headless Chrome) | Page requires JS to render job listings | High - full browser |
| AI/LLM parsing | Selectors keep breaking, or zero-config scraping of a new site | Medium - ~$0.01-0.05/page API cost |

**Recommendation:** Before writing Selenium code for a new scraper, always check if the page works with plain `httpx` first. Many "dynamic" pages embed data as JSON inside `<script>` tags.

### Scraper Registry Pattern

Replace the hard-coded dictionary in `scraper_service.py` with decorator-based auto-registration:

```python
# scrapers/registry.py
_SCRAPER_REGISTRY: Dict[str, Type[BaseScraper]] = {}

def register_scraper(name: str):
    def decorator(cls: Type[BaseScraper]):
        _SCRAPER_REGISTRY[name.lower()] = cls
        return cls
    return decorator

def get_scraper(name: str) -> BaseScraper:
    cls = _SCRAPER_REGISTRY.get(name.lower())
    if cls is None:
        raise ValueError(f"No scraper registered for '{name}'")
    return cls()
```

```python
# scrapers/implementations/cdprojektred.py
@register_scraper("cd projekt red")
class CDProjektRedScraper(BaseScraper):
    ...
```

Auto-discovery in `scrapers/__init__.py` via `pkgutil.iter_modules()` triggers all `@register_scraper` decorators on import.

**Adding a new scraper requires:** (1) create file in `scrapers/implementations/`, (2) decorate with `@register_scraper("name")`, (3) add company row to DB. No other files change.

### Browser Management

Centralize Selenium setup into a context manager (`scrapers/browser.py`):

```python
@contextmanager
def create_browser():
    # Chrome options setup (headless, no-sandbox, etc.)
    driver = webdriver.Chrome(service=Service(ChromeDriverManager().install()), options=opts)
    try:
        yield driver
    finally:
        driver.quit()
```

Eliminates ~10 lines of duplicated Chrome setup per scraper.

### AI Parsing Fallback (Phase 5)

A utility function accepting raw HTML, returning structured job data via Claude/OpenAI API. Opt-in per company via a `parser_type` field on `CompanyCareerPage` (`"selector"` default or `"ai"`).

---

## 4. Database Strategy

### Local: SQLite + Alembic

SQLite stays for local dev. Add Alembic for migration management. Remove `Base.metadata.create_all()` and replace with `alembic upgrade head` at startup.

### Azure: PostgreSQL Flexible Server

- **Why PostgreSQL over Azure SQL (MSSQL):** `psycopg2` is pip-installable; MSSQL requires `pyodbc` + ODBC drivers which are painful in Docker containers. PostgreSQL has first-class Python ecosystem support.
- **Tier:** Burstable B1ms (1 vCore, 2 GB RAM) ~$13/month
- Connection: `postgresql+psycopg2://user:pass@host:5432/db?sslmode=require`

### AWS: RDS PostgreSQL

Identical from the application side. Only the connection string changes. Same Alembic migrations, same driver.

### Connection String Abstraction

```python
# config.py
class Settings(BaseSettings):
    database_url: str = "sqlite:///./careers.db"

    @property
    def engine_kwargs(self) -> dict:
        if "sqlite" in self.database_url:
            return {"connect_args": {"check_same_thread": False}}
        return {"pool_size": 5, "max_overflow": 10, "pool_pre_ping": True}
```

One setting, one connection string, works everywhere.

---

## 5. Azure Deployment Strategy

### Hosting: Azure Container Apps (ACA)

| Option | Fits This App? | Cost | Complexity |
|--------|---------------|------|------------|
| App Service | Adequate | ~$13/mo (B1) | Low |
| **Container Apps** | **Best fit** | **~$5-15/mo (consumption)** | **Low-Medium** |
| Functions | Poor fit (no Selenium, cold starts) | ~$1-5/mo | High |
| AKS | Massive overkill | ~$70+/mo | Very High |

**Why ACA wins:**
- Consumption-based pricing (idle most of the time, scrapes 1x/hour)
- Single container runs both uvicorn + APScheduler
- Built-in HTTPS/TLS termination
- Min replicas = 1 keeps the scheduler alive

### Selenium: In-Container

Run Chrome in the same container. Adding a separate Selenium Grid adds operational complexity for zero benefit at 3-5 scrapers running once per hour. Container needs ~1 vCPU, 2 GB RAM.

### Container Setup

**Dockerfile:** Python 3.12-slim base, install `chromium` + `chromium-driver` via apt, pip install the app, copy source.

**docker-compose.yml (local dev):** App container + PostgreSQL 16 Alpine. Enables developing against a real PostgreSQL locally.

### Azure Resources Needed

| Resource | Tier | Estimated Cost |
|----------|------|---------------|
| Azure Container Registry | Basic | ~$5/mo |
| Azure Container Apps | Consumption plan | ~$5-15/mo |
| Azure Database for PostgreSQL | Flexible Server B1ms | ~$13/mo |
| Azure Key Vault | Free tier (<10k txn/mo) | $0 |
| Managed Identity | System-assigned | $0 |
| **Total** | | **~$23-33/mo** |

---

## 6. Configuration Management

### Enhanced config.py

```python
class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_prefix="CAREERS_", env_file=".env")

    environment: str = "development"       # development | production
    debug: bool = False
    database_url: str = "sqlite:///./careers.db"
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    search_keywords: str = "python,backend,developer"
    scrape_interval_minutes: int = 60
    scraper_timeout_seconds: int = 30
    scraper_retry_count: int = 2
    dashboard_api_key: Optional[str] = None  # None = no auth (dev)
    ai_api_key: Optional[str] = None
    azure_keyvault_url: Optional[str] = None
```

`env_prefix="CAREERS_"` means env vars are `CAREERS_DATABASE_URL`, `CAREERS_TELEGRAM_BOT_TOKEN`, etc. Prevents collisions in container environments.

### Azure Key Vault Integration

At startup, before `Settings()` instantiation: if `CAREERS_AZURE_KEYVAULT_URL` is set, fetch secrets from Key Vault using `DefaultAzureCredential` and inject as env vars. The app itself is unaware of Key Vault - it always reads env vars.

---

## 7. Logging & Observability

### Replace print() with Python logging

`core/logging.py`: Configure stdlib `logging` with:
- Human-readable format in development
- JSON structured output in production (for Azure Log Analytics ingestion)
- Suppress noisy libraries (selenium, urllib3, apscheduler)

Every module: `logger = logging.getLogger(__name__)` with appropriate levels.

### What to Monitor

| Metric | How | Why |
|--------|-----|-----|
| Scraping success/failure per company | Log at INFO/ERROR | Know when a scraper breaks |
| Jobs found per cycle | Structured log | Detect page structure changes (0 jobs = broken) |
| Scraping duration | Log elapsed time | Detect performance degradation |
| Notification delivery | Log at INFO/ERROR | Know when Telegram is down |
| API response times | Application Insights (Phase 4) | Dashboard performance |

### Azure Application Insights (Phase 4)

Integrate via `azure-monitor-opentelemetry` for automatic request tracing, dependency tracking, and exception logging.

---

## 8. Security

- **Dashboard auth:** API key via `X-API-Key` header. Set via env var. No auth in dev (key=None). Swappable to JWT/OAuth2 for multi-user later.
- **HTML injection:** `html.escape()` on all job data before Telegram HTML messages. `textContent` instead of `innerHTML` in dashboard JS.
- **Secrets:** `.env` for local, Azure Key Vault for production. Never commit secrets.

---

## 9. Design Patterns

| Pattern | Where | Benefit |
|---------|-------|---------|
| **Strategy** | `BaseScraper` ABC + implementations | Each scraper encapsulates its own parsing logic |
| **Registry/Factory** | `@register_scraper` decorator + `get_scraper()` | Zero-touch scraper discovery, no manual imports |
| **Repository** | `JobRepository`, `CompanyRepository` | Isolates SQL from business logic, enables testing |
| **Context Manager** | `browser.py` `create_browser()` | Guarantees resource cleanup (no driver leaks) |
| **Observer** | `NotificationManager` with channels | Decouple scraping from notification delivery |

---

## 10. Phased Implementation Roadmap

### Phase 1: Foundation

Restructure and add tooling. No new features.

- [ ] Restructure project into `src/careers_scraper/` package layout
- [ ] Replace all `print()` with `logging` (`core/logging.py`)
- [ ] Refactor `config.py` with `env_prefix`, new settings fields
- [ ] Set up Alembic migrations (initial migration from current models)
- [ ] Create `pyproject.toml` (replace `requirements.txt`)
- [ ] Set up pytest with `conftest.py` fixtures (in-memory SQLite, TestClient)
- [ ] Extract HTML/CSS/JS from `web_app.py` into `web/static/` files
- [ ] Create `db/repositories/` (JobRepository, CompanyRepository with pagination)
- [ ] Write initial tests (config, repositories, API endpoints)

### Phase 2: Core Stability

Make existing scrapers reliable.

- [ ] Fix Uklon scraper (inspect real page, write correct selectors)
- [ ] Centralize browser management (`scrapers/browser.py` context manager)
- [ ] Implement scraper registry (`@register_scraper` + auto-discovery)
- [ ] Add retry logic with `tenacity` in `ScraperService`
- [ ] Fix async/sync mismatch in Telegram notifier
- [ ] Add input sanitization (HTML escaping in Telegram + web)
- [ ] Create custom exception hierarchy (`core/exceptions.py`)
- [ ] Write unit tests for scrapers using saved HTML fixtures

### Phase 3: Production Readiness

Make it deployable.

- [ ] Create `Dockerfile` (Python 3.12-slim + Chromium)
- [ ] Create `docker-compose.yml` (app + PostgreSQL for local dev)
- [ ] Add health check endpoints (`/health`, `/ready`)
- [ ] Add dashboard API key authentication
- [ ] Add API pagination (`offset`/`limit` on `/api/jobs`)
- [ ] Add graceful shutdown (SIGTERM/SIGINT handling)
- [ ] Validate all scrapers work inside Docker container
- [ ] Set up GitHub Actions CI (pytest + Docker build)

### Phase 4: Cloud Deployment

Deploy to Azure.

- [ ] Provision Azure resources (ACR, ACA, PostgreSQL, Key Vault)
- [ ] Configure Key Vault secrets + managed identity
- [ ] Deploy to Azure Container Apps
- [ ] Verify production: dashboard + scraping + Telegram notifications
- [ ] Set up Azure Monitor alerts (container restart, health check failure)

### Phase 5: Enhancement (Ongoing)

- [ ] Implement AI parsing fallback (`ai_parser.py`)
- [ ] Add new scrapers (one file + one decorator + one DB row each)
- [ ] Multi-user support (User model, JWT auth, per-user keywords)
- [ ] Dashboard redesign (htmx + TailwindCSS or React)
- [ ] Azure Application Insights integration
- [ ] Consider Playwright migration if Selenium is unstable in containers
- [ ] AWS deployment option (ECS Fargate + RDS PostgreSQL)

---

## Critical Files to Modify

| File | What Changes | Why |
|------|-------------|-----|
| `scraper_service.py` | Remove hard-coded registry, use repositories, add retry, decouple notifications | Most architectural improvements converge here |
| `database.py` | Split into `db/engine.py`, `db/session.py`, `db/models.py`, `db/repositories/` | Foundation for Alembic + repository pattern |
| `scrapers/base_scraper.py` | Extend with ScrapeMethod enum, support registry decorator | Foundation for strategy + factory patterns |
| `web_app.py` | Extract to `web/app.py` + routes + static files, add auth + pagination | Maintainability + production readiness |
| `config.py` | Add env_prefix, new settings, validators | Every module depends on this |
| `telegram_notifier.py` | Fix async, add HTML escaping, restructure as notification channel | Security + reliability |

---

## Verification Plan

After each phase, verify:
1. **Phase 1:** `pytest` passes, `alembic upgrade head` creates tables, dashboard loads from static files
2. **Phase 2:** All 3 scrapers return real job data, retry works on simulated failure, registry auto-discovers scrapers
3. **Phase 3:** `docker-compose up` starts app + PostgreSQL, `/health` returns 200, dashboard requires API key, jobs paginate correctly
4. **Phase 4:** Azure URL loads dashboard, scraping runs on schedule, Telegram notifications arrive, Key Vault secrets resolve
5. **Phase 5:** AI parser extracts jobs from raw HTML, new scraper added in <5 minutes
