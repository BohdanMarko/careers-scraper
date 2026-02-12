# Phase 3: Production Readiness

Make the application deployable with Docker, authentication, and CI.

**Prerequisite:** Phase 2 (Scraper Reliability) must be complete.

---

## Scope

- Create `Dockerfile` (Python 3.12-slim + Chromium)
- Create `docker-compose.yml` (app + PostgreSQL for local dev)
- Add health check endpoints (`/health`, `/ready`)
- Add dashboard API key authentication
- Add API pagination on `/api/jobs`
- Add graceful shutdown (SIGTERM/SIGINT handling)
- Validate all scrapers work inside Docker
- Set up GitHub Actions CI

## Non-Goals

- No cloud infrastructure provisioning (Phase 4)
- No Azure-specific configuration (Phase 4)
- No AI parsing or new features (Phase 5)
- No multi-user support (Phase 5)

---

## Technical Design

### 1. Dockerfile

```dockerfile
FROM python:3.12-slim

# Install Chromium for Selenium scrapers
RUN apt-get update && apt-get install -y \
    chromium \
    chromium-driver \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app
COPY pyproject.toml .
RUN pip install --no-cache-dir .

COPY src/ src/
COPY alembic/ alembic/
COPY alembic.ini .

EXPOSE 8000

CMD ["python", "-m", "careers_scraper.main"]
```

Container needs ~1 vCPU, 2 GB RAM (Chromium is memory-hungry).

### 2. docker-compose.yml

```yaml
services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - CAREERS_DATABASE_URL=postgresql+psycopg2://careers:careers@db:5432/careers
      - CAREERS_ENVIRONMENT=development
    depends_on:
      db:
        condition: service_healthy
  db:
    image: postgres:16-alpine
    environment:
      POSTGRES_USER: careers
      POSTGRES_PASSWORD: careers
      POSTGRES_DB: careers
    ports:
      - "5432:5432"
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U careers"]
      interval: 5s
      timeout: 5s
      retries: 5
    volumes:
      - pgdata:/var/lib/postgresql/data

volumes:
  pgdata:
```

Enables developing against PostgreSQL locally to catch SQLite-vs-PostgreSQL differences before cloud deployment.

### 3. Health Check Endpoints

```python
# src/careers_scraper/web/routes/health.py
@router.get("/health")
def health():
    """Liveness probe - app is running."""
    return {"status": "healthy"}

@router.get("/ready")
def ready(db: Session = Depends(get_db)):
    """Readiness probe - app can serve requests."""
    db.execute(text("SELECT 1"))
    return {"status": "ready", "database": "connected"}
```

Used by Docker `HEALTHCHECK`, Azure Container Apps probes, and monitoring.

### 4. API Key Authentication

```python
# src/careers_scraper/web/auth.py
from fastapi import Security, HTTPException
from fastapi.security import APIKeyHeader

api_key_header = APIKeyHeader(name="X-API-Key", auto_error=False)

def require_api_key(api_key: str = Security(api_key_header)):
    settings = get_settings()
    if settings.dashboard_api_key is None:
        return  # No auth in dev mode
    if api_key != settings.dashboard_api_key:
        raise HTTPException(status_code=401, detail="Invalid API key")
```

Configuration via `Settings`:
- `dashboard_api_key: Optional[str] = None` -- `None` means no auth (dev mode)
- Set `CAREERS_DASHBOARD_API_KEY` in production

Applied to all routes except `/health` and `/ready`.

### 5. API Pagination

```python
# src/careers_scraper/web/routes/jobs.py
@router.get("/api/jobs")
def get_jobs(
    offset: int = Query(0, ge=0),
    limit: int = Query(50, ge=1, le=200),
    db: Session = Depends(get_db)
):
    repo = JobRepository(db)
    jobs = repo.get_jobs(offset=offset, limit=limit)
    total = repo.count()
    return {"jobs": jobs, "total": total, "offset": offset, "limit": limit}
```

Default page size: 50. Max: 200. Prevents loading all jobs into memory.

### 6. Graceful Shutdown

```python
# src/careers_scraper/main.py
import signal

def main():
    setup_logging(settings.environment)
    scheduler = create_scheduler()
    scheduler.start()

    def shutdown(signum, frame):
        logger.info("Shutting down gracefully...")
        scheduler.shutdown(wait=False)
        sys.exit(0)

    signal.signal(signal.SIGTERM, shutdown)
    signal.signal(signal.SIGINT, shutdown)

    uvicorn.run(app, host=settings.web_host, port=settings.web_port)
```

Ensures APScheduler stops cleanly and doesn't leave orphaned Chrome processes.

### 7. GitHub Actions CI

```yaml
# .github/workflows/ci.yml
name: CI
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.12"
      - run: pip install -e ".[dev]"
      - run: pytest --cov=src/careers_scraper
  docker:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: docker build -t careers-scraper .
```

Two jobs: run tests + verify Docker build succeeds.

---

## Data Model Changes

None. No schema changes in this phase.

---

## API Changes

| Endpoint | Change |
|----------|--------|
| `GET /api/jobs` | Add `offset` and `limit` query params, response includes `total` count |
| `GET /health` | **New** -- liveness probe |
| `GET /ready` | **New** -- readiness probe with DB check |
| All other routes | Require `X-API-Key` header when `dashboard_api_key` is configured |

---

## Security

- **Dashboard auth:** API key via `X-API-Key` header. No auth when key is `None` (dev). Swappable to JWT/OAuth2 for multi-user later (Phase 5).
- **HTML injection:** Verify `textContent` usage in dashboard JS (done in Phase 2). Verify `html.escape()` in Telegram messages (done in Phase 2).
- **Secrets in Docker:** Pass via environment variables, never bake into image. `.env` file for docker-compose, Azure Key Vault for production (Phase 4).

---

## Files to Modify

| File | What Changes | Why |
|------|-------------|-----|
| `web/app.py` | Add auth middleware, mount health routes | Security + monitoring |
| `web/routes/jobs.py` | Add pagination params | Performance |
| `main.py` | Add signal handlers for graceful shutdown | Reliability |

## New Files

| File | Purpose |
|------|---------|
| `Dockerfile` | Container image definition |
| `docker-compose.yml` | Local dev with PostgreSQL |
| `web/auth.py` | API key authentication |
| `web/routes/health.py` | Health check endpoints |
| `web/schemas.py` | Pydantic response models for pagination |
| `.github/workflows/ci.yml` | GitHub Actions CI pipeline |

---

## Implementation Checklist

- [ ] Create `Dockerfile` with Python 3.12-slim + Chromium
- [ ] Create `docker-compose.yml` with app + PostgreSQL
- [ ] Create `web/routes/health.py` with `/health` and `/ready` endpoints
- [ ] Create `web/auth.py` with API key middleware
- [ ] Add `dashboard_api_key` to `Settings`
- [ ] Apply auth middleware to all routes except health checks
- [ ] Add `offset`/`limit` params to `GET /api/jobs`
- [ ] Create `web/schemas.py` with pagination response models
- [ ] Add graceful shutdown signal handlers in `main.py`
- [ ] Verify all 3 scrapers work inside Docker container
- [ ] Verify `docker-compose up` starts app + PostgreSQL successfully
- [ ] Create `.github/workflows/ci.yml`
- [ ] Add `psycopg2-binary` to `pyproject.toml` dependencies
- [ ] Update `.env.example` with `CAREERS_DASHBOARD_API_KEY`

---

## Acceptance Criteria

1. `docker-compose up` starts app + PostgreSQL, dashboard loads at `localhost:8000`
2. `GET /health` returns 200 with `{"status": "healthy"}`
3. `GET /ready` returns 200 with database connection confirmed
4. Dashboard requires `X-API-Key` header when `CAREERS_DASHBOARD_API_KEY` is set
5. `GET /api/jobs?offset=0&limit=10` returns paginated results with `total` count
6. All 3 scrapers successfully scrape inside Docker container
7. `SIGTERM` triggers clean shutdown (no orphaned Chrome processes)
8. GitHub Actions CI passes (pytest + Docker build)

---

## Implementation Notes

- Use `psycopg2-binary` for PostgreSQL driver (avoids compilation issues in Docker)
- The Dockerfile installs `chromium` and `chromium-driver` via apt -- no ChromeDriverManager in production
- Update `browser.py` to detect if chromedriver is available system-wide (Docker) vs needs `ChromeDriverManager` (local dev)
- `docker-compose.yml` is for local dev only -- production uses Azure Container Apps (Phase 4)
