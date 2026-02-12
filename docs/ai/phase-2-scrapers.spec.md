# Phase 2: Scraper Reliability

Make existing scrapers reliable and establish patterns for adding new ones.

**Prerequisite:** Phase 1 (Foundation) must be complete.

---

## Scope

- Fix the broken Uklon scraper
- Centralize browser management into a shared context manager
- Implement decorator-based scraper registry with auto-discovery
- Add retry logic with `tenacity`
- Fix async/sync mismatch in Telegram notifier
- Add input sanitization (HTML escaping)
- Create custom exception hierarchy
- Write unit tests for scrapers using saved HTML fixtures

## Non-Goals

- No new scrapers (adding scrapers becomes trivial after this phase)
- No Docker or deployment (Phase 3)
- No API changes (Phase 3)
- No cloud infrastructure (Phase 4)
- No AI parsing (Phase 5)

---

## Technical Design

### 1. Scraper Registry Pattern

Replace the hard-coded dictionary in `scraper_service.py` with decorator-based auto-registration:

```python
# src/careers_scraper/scrapers/registry.py
from typing import Dict, Type
from .base import BaseScraper

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

def get_registered_scrapers() -> Dict[str, Type[BaseScraper]]:
    return dict(_SCRAPER_REGISTRY)
```

Auto-discovery in `scrapers/__init__.py` via `pkgutil.iter_modules()` triggers all `@register_scraper` decorators on import.

**Adding a new scraper after this phase:** (1) create file in `scrapers/implementations/`, (2) decorate with `@register_scraper("name")`, (3) add company row to DB. No other files change.

### 2. Scraper Method Selection

Extend `BaseScraper` with a `ScrapeMethod` enum:

```python
# src/careers_scraper/scrapers/base.py
from enum import Enum

class ScrapeMethod(Enum):
    SELENIUM = "selenium"
    HTTP = "http"
    AI = "ai"  # Phase 5

class BaseScraper(ABC):
    method: ScrapeMethod = ScrapeMethod.SELENIUM

    @abstractmethod
    def scrape(self) -> list[dict]:
        ...
```

| Technique | Use When | Cost |
|-----------|----------|------|
| `httpx` + BeautifulSoup | Content is in initial HTML (server-rendered) | Low - no browser |
| Selenium (headless Chrome) | Page requires JS to render job listings | High - full browser |
| AI/LLM parsing | Selectors keep breaking, or zero-config scraping (Phase 5) | Medium - API cost |

**Recommendation:** Before writing Selenium code for a new scraper, always check if the page works with plain `httpx` first. Many "dynamic" pages embed data as JSON inside `<script>` tags.

### 3. Browser Management

Centralize Selenium setup into a context manager:

```python
# src/careers_scraper/scrapers/browser.py
from contextlib import contextmanager

@contextmanager
def create_browser():
    opts = webdriver.ChromeOptions()
    opts.add_argument("--headless")
    opts.add_argument("--no-sandbox")
    opts.add_argument("--disable-dev-shm-usage")
    driver = webdriver.Chrome(
        service=Service(ChromeDriverManager().install()),
        options=opts
    )
    try:
        yield driver
    finally:
        driver.quit()
```

Eliminates ~10 lines of duplicated Chrome setup per scraper. Each scraper's `scrape()` method uses `with create_browser() as driver:`.

### 4. Retry Logic

Add `tenacity` retry to `ScraperService.run_cycle()`:

```python
from tenacity import retry, stop_after_attempt, wait_exponential

@retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, max=30))
def _scrape_company(self, company, scraper):
    return scraper.scrape()
```

Configuration via `Settings`:
- `scraper_timeout_seconds: int = 30`
- `scraper_retry_count: int = 2`

### 5. Fix Uklon Scraper

Inspect the real Uklon careers page, identify correct CSS selectors for job listings, titles, and URLs. Replace placeholder selectors (`[class*='vacancy']`, `[class*='job']`).

### 6. Fix Telegram Notifier

**Problem:** `send_job_notification_sync()` calls `asyncio.run()` per message, creating a new event loop each time. Crashes if called from within an existing async context.

**Fix:** Restructure as a notification channel:

```python
# src/careers_scraper/notifications/telegram.py
class TelegramChannel(NotificationChannel):
    def send(self, job: dict) -> bool:
        message = self._format_message(job)
        # Use httpx sync client instead of asyncio
        response = httpx.post(
            f"https://api.telegram.org/bot{self.token}/sendMessage",
            json={"chat_id": self.chat_id, "text": message, "parse_mode": "HTML"}
        )
        return response.is_success
```

### 7. Input Sanitization

- **Telegram messages:** `html.escape()` on all job data before inserting into HTML-formatted messages
- **Web dashboard JS:** Use `textContent` instead of `innerHTML` when rendering job data

### 8. Custom Exceptions

```python
# src/careers_scraper/core/exceptions.py
class CareersScraperError(Exception):
    """Base exception for all application errors."""

class ScraperError(CareersScraperError):
    """Raised when a scraper fails."""

class ScraperNotFoundError(CareersScraperError):
    """Raised when no scraper is registered for a company."""

class NotificationError(CareersScraperError):
    """Raised when notification delivery fails."""

class DatabaseError(CareersScraperError):
    """Raised when a database operation fails."""
```

Replace bare `except Exception` patterns with specific exception types.

---

## Data Model Changes

Add `parser_type` field to `CompanyCareerPage` model (for future AI parsing opt-in):

```python
parser_type: str = Column(String, default="selector")  # "selector" or "ai" (Phase 5)
```

Alembic migration required.

---

## API Changes

None. Internal changes only.

---

## Files to Modify

| File | What Changes | Why |
|------|-------------|-----|
| `services/scraper_service.py` | Remove hard-coded registry, use `get_scraper()`, add retry | Most changes converge here |
| `scrapers/base.py` | Add `ScrapeMethod` enum, update ABC | Foundation for strategy pattern |
| `scrapers/implementations/uklon.py` | Replace placeholder selectors with real ones | Fix broken scraper |
| `notifications/telegram.py` | Fix async, add HTML escaping, use httpx sync | Security + reliability |
| All scraper files | Use `create_browser()` context manager | Eliminate duplication |

## New Files

| File | Purpose |
|------|---------|
| `scrapers/registry.py` | `@register_scraper` decorator + `get_scraper()` factory |
| `scrapers/browser.py` | Shared Selenium context manager |
| `scrapers/http_client.py` | httpx client wrapper for static scrapers |
| `core/exceptions.py` | Custom exception hierarchy |
| `notifications/base.py` | `NotificationChannel` ABC |
| `notifications/manager.py` | `NotificationManager` dispatcher |

---

## Implementation Checklist

- [ ] Create `scrapers/registry.py` with `@register_scraper` decorator
- [ ] Add auto-discovery in `scrapers/__init__.py` via `pkgutil.iter_modules()`
- [ ] Add `ScrapeMethod` enum to `scrapers/base.py`
- [ ] Create `scrapers/browser.py` context manager
- [ ] Create `scrapers/http_client.py` for static page scraping
- [ ] Refactor all 3 scrapers to use `@register_scraper` and `create_browser()`
- [ ] Fix Uklon scraper with correct CSS selectors
- [ ] Add `tenacity` retry in `ScraperService`
- [ ] Create `notifications/base.py` ABC and `notifications/manager.py`
- [ ] Refactor Telegram notifier to sync httpx, add HTML escaping
- [ ] Create `core/exceptions.py` with custom exception hierarchy
- [ ] Replace bare `except Exception` with specific exception types
- [ ] Remove hard-coded scraper registry from `scraper_service.py`
- [ ] Add `parser_type` field to `CompanyCareerPage` model + Alembic migration
- [ ] Write unit tests for scrapers using saved HTML fixture files
- [ ] Write unit tests for registry auto-discovery
- [ ] Add `tenacity` to `pyproject.toml` dependencies

---

## Acceptance Criteria

1. All 3 scrapers return real job data (including Uklon)
2. `get_registered_scrapers()` returns all 3 scrapers without manual registry
3. Retry works on simulated network failure (test with mock)
4. Browser context manager properly cleans up (no driver leaks)
5. Telegram messages have HTML-escaped job titles
6. Web dashboard uses `textContent` (no innerHTML injection)
7. Adding a new scraper requires only: new file + decorator + DB row
8. All new and existing tests pass

---

## Implementation Notes

- Install `tenacity` as a new dependency (lightweight, no transitive deps)
- The httpx sync client replaces the async Telegram approach -- simpler and avoids event loop issues
- Save real HTML pages as test fixtures in `tests/fixtures/` for scraper unit tests
- `beautifulsoup4` and `requests` are in `requirements.txt` but unused -- remove them if httpx replaces their intended use
