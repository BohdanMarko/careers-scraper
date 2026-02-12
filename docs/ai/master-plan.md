# Careers Scraper: Architecture & Roadmap

## 1. Current State

A functional prototype (~550 lines Python, 12 source files) with: FastAPI web dashboard, APScheduler background scraping, Selenium-based scrapers with an ABC base class, Telegram notifications, and SQLAlchemy/SQLite persistence. Three scrapers (Uklon, CD Projekt Red, Growe) are implemented.

**Phase:** Pre-Phase 1 (Prototype). See phase spec files for implementation details.

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
│       ├── core/
│       │   ├── __init__.py
│       │   ├── logging.py              # Structured logging setup
│       │   └── exceptions.py           # Custom exception hierarchy
│       ├── db/
│       │   ├── __init__.py
│       │   ├── engine.py              # Engine factory (SQLite/PostgreSQL)
│       │   ├── session.py             # Session management, get_db
│       │   ├── models.py             # SQLAlchemy ORM models
│       │   └── repositories/
│       │       ├── __init__.py
│       │       ├── job_repository.py  # CRUD for Job with pagination
│       │       └── company_repository.py
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
│       ├── notifications/
│       │   ├── __init__.py
│       │   ├── base.py               # NotificationChannel ABC
│       │   ├── telegram.py           # Telegram implementation
│       │   └── manager.py            # Dispatches to active channels
│       ├── services/
│       │   ├── __init__.py
│       │   └── scraper_service.py    # Orchestration: scrape -> dedupe -> notify
│       ├── scheduler/
│       │   ├── __init__.py
│       │   └── scheduler.py          # APScheduler wrapper with health tracking
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
├── alembic/
│   ├── env.py
│   └── versions/
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

---

## 3. Key Design Decisions

| Decision | Choice | Justification |
|----------|--------|---------------|
| Monolith vs microservices | **Single process monolith** | Solo developer; web + scheduler + scrapers in one process is simpler to develop, debug, and deploy. |
| APScheduler vs Celery | **APScheduler** | Celery requires Redis/RabbitMQ broker + separate worker. APScheduler runs in-process. |
| Selenium vs Playwright | **Keep Selenium (for now)** | Already works. `browser.py` abstraction allows future migration. |
| In-process events vs queue | **In-process NotificationManager** | One event type, 1-2 handlers. No benefit from Redis pub/sub at this scale. |
| SQLite vs PostgreSQL | **Both** | SQLite for local dev, PostgreSQL for cloud. Same ORM, same migrations. |

---

## 4. Design Patterns

| Pattern | Where | Benefit |
|---------|-------|---------|
| **Strategy** | `BaseScraper` ABC + implementations | Each scraper encapsulates its own parsing logic |
| **Registry/Factory** | `@register_scraper` decorator + `get_scraper()` | Zero-touch scraper discovery, no manual imports |
| **Repository** | `JobRepository`, `CompanyRepository` | Isolates SQL from business logic, enables testing |
| **Context Manager** | `browser.py` `create_browser()` | Guarantees resource cleanup (no driver leaks) |
| **Observer** | `NotificationManager` with channels | Decouple scraping from notification delivery |

---

## 5. Phased Roadmap (Overview)

Each phase has a dedicated spec file with full implementation details, checklists, and acceptance criteria.

| Phase | Title | Focus | Spec File |
|-------|-------|-------|-----------|
| 1 | Foundation | Restructure, config, DB, logging, tests | [`phase-1-core.spec.md`](phase-1-core.spec.md) |
| 2 | Scraper Reliability | Registry, browser, retry, fixes | [`phase-2-scrapers.spec.md`](phase-2-scrapers.spec.md) |
| 3 | Production Readiness | Docker, auth, pagination, CI | [`phase-3-dashboard.spec.md`](phase-3-dashboard.spec.md) |
| 4 | Cloud Deployment | Azure ACA, PostgreSQL, Key Vault | [`phase-4-cloud.spec.md`](phase-4-cloud.spec.md) |
| 5 | Enhancement | AI parsing, multi-user, monitoring | [`phase-5-observability.spec.md`](phase-5-observability.spec.md) |

---

## 6. Cloud Strategy (Summary)

**Primary target:** Azure (consumption-based pricing, ~$23-33/month)

| Resource | Tier | Est. Cost |
|----------|------|-----------|
| Azure Container Registry | Basic | ~$5/mo |
| Azure Container Apps | Consumption | ~$5-15/mo |
| Azure Database for PostgreSQL | Flexible Server B1ms | ~$13/mo |
| Azure Key Vault | Free tier | $0 |

**Future:** AWS compatibility (ECS Fargate + RDS PostgreSQL). Same application code, different infrastructure provisioning.

See [`phase-4-cloud.spec.md`](phase-4-cloud.spec.md) for full deployment details.

---

## 7. What NOT to Add

- Don't add Celery (overkill for hourly scraping)
- Don't split into microservices
- Don't add Redis/RabbitMQ
- Don't create abstractions until needed
- Don't add features beyond current phase scope
- Don't over-engineer for hypothetical scale
