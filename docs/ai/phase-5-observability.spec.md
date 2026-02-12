# Phase 5: Enhancement

Ongoing improvements after the application is deployed and stable.

**Prerequisite:** Phase 4 (Cloud Deployment) must be complete.

---

## Scope

- Implement AI parsing fallback for fragile scrapers
- Add new scrapers (trivial after Phase 2 registry)
- Multi-user support with JWT authentication
- Dashboard redesign
- Azure Application Insights integration
- Consider Playwright migration
- AWS deployment option

## Non-Goals

- This phase is open-ended -- items are prioritized but not all required
- No breaking changes to existing scraper interface

---

## Technical Design

### 1. AI Parsing Fallback

A utility function that accepts raw HTML and returns structured job data via Claude or OpenAI API. Opt-in per company via the `parser_type` field on `CompanyCareerPage` (`"selector"` default or `"ai"`).

```python
# src/careers_scraper/scrapers/ai_parser.py
async def parse_jobs_with_ai(html: str, company_name: str) -> list[dict]:
    """Send raw HTML to LLM API, return structured job listings."""
    prompt = f"""Extract job listings from this {company_name} careers page.
    Return JSON array with fields: title, url, location, department."""
    # Call Claude/OpenAI API
    ...
```

**Cost:** ~$0.01-0.05 per page (depends on HTML size and model).

**When to use:** When CSS selectors keep breaking for a site, or for zero-config scraping of a new company's careers page.

Configuration:
- `ai_api_key: Optional[str] = None` in `Settings`
- `CAREERS_AI_API_KEY` env var (stored in Key Vault)

### 2. Adding New Scrapers

After Phase 2, adding a scraper is trivial:

1. Create file in `src/careers_scraper/scrapers/implementations/`
2. Decorate with `@register_scraper("company name")`
3. Add company row to database
4. Auto-discovery handles the rest

No spec needed per scraper -- it's a routine operation.

### 3. Multi-User Support

Extend the data model and auth system:

- **User model:** `id`, `email`, `hashed_password`, `keywords`, `telegram_chat_id`
- **Auth:** Replace API key with JWT tokens (access + refresh)
- **Per-user keywords:** Each user configures their own search keywords
- **Per-user notifications:** Telegram chat ID per user, matched against user-specific keywords

This is a significant feature requiring:
- User registration/login endpoints
- Password hashing (passlib + bcrypt)
- JWT token generation/validation (python-jose)
- Database migration for User table
- Notification routing per user

### 4. Dashboard Redesign

Options (choose one when implementing):
- **htmx + TailwindCSS:** Server-rendered, minimal JS, fast iteration
- **React/Vue SPA:** Full client-side rendering, richer UX

Either way, replace the current vanilla JS with a proper frontend build.

### 5. Azure Application Insights

Integrate via `azure-monitor-opentelemetry` for:
- Automatic request tracing
- Dependency tracking (DB queries, HTTP calls)
- Exception logging with stack traces
- Custom metrics (jobs found per cycle, scraper duration)

```python
from azure.monitor.opentelemetry import configure_azure_monitor

configure_azure_monitor(connection_string=settings.appinsights_connection_string)
```

### What to Monitor

| Metric | How | Why |
|--------|-----|-----|
| Scraping success/failure per company | Custom metric | Know when a scraper breaks |
| Jobs found per cycle | Custom metric | Detect page structure changes (0 jobs = broken) |
| Scraping duration | Custom metric | Detect performance degradation |
| Notification delivery | Custom metric | Know when Telegram is down |
| API response times | Application Insights auto-instrumentation | Dashboard performance |

### 6. Playwright Migration

Consider if Selenium proves unstable in Docker containers. `browser.py` abstraction (Phase 2) makes this a localized change -- only the context manager implementation changes, scraper code stays the same.

### 7. AWS Deployment Option

Same application code, different infrastructure:
- **Hosting:** ECS Fargate (consumption-based)
- **Database:** RDS PostgreSQL
- **Secrets:** AWS Secrets Manager
- **Registry:** ECR

Only the Key Vault bootstrap in `config.py` needs an AWS equivalent. All other code is cloud-agnostic.

---

## Data Model Changes

| Change | Details |
|--------|---------|
| User table | `id`, `email`, `hashed_password`, `keywords`, `telegram_chat_id`, `created_at` |
| Job-User relationship | Optional: per-user job notification tracking |

---

## API Changes

| Endpoint | Change |
|----------|--------|
| `POST /auth/register` | **New** -- user registration |
| `POST /auth/login` | **New** -- JWT token generation |
| `GET /api/profile` | **New** -- user profile and keyword management |
| `PUT /api/profile/keywords` | **New** -- update search keywords |

---

## New Dependencies

| Package | Purpose |
|---------|---------|
| `azure-monitor-opentelemetry` | Application Insights integration |
| `anthropic` or `openai` | AI parsing API client |
| `python-jose` | JWT token handling (multi-user) |
| `passlib[bcrypt]` | Password hashing (multi-user) |

---

## Implementation Checklist

- [ ] Implement `ai_parser.py` with Claude/OpenAI integration
- [ ] Add `parser_type` field usage in `ScraperService` (field added in Phase 2)
- [ ] Add new scrapers as needed (one file + decorator each)
- [ ] Design and implement User model + JWT auth
- [ ] Create registration and login endpoints
- [ ] Implement per-user keyword matching and notification routing
- [ ] Integrate Azure Application Insights
- [ ] Add custom metrics for scraping operations
- [ ] Evaluate and implement dashboard redesign
- [ ] Evaluate Playwright vs Selenium stability in containers
- [ ] Document AWS deployment option

---

## Acceptance Criteria

1. AI parser extracts jobs from raw HTML with >90% accuracy
2. New scraper can be added in <5 minutes (file + decorator + DB row)
3. Multiple users can register, login, and receive personalized notifications
4. Application Insights shows request traces, exceptions, and custom metrics
5. Dashboard is visually improved and responsive

---

## Implementation Notes

- Phase 5 items are independent and can be implemented in any order
- AI parsing cost should be monitored -- set a monthly budget alert
- Multi-user support is the largest single feature in the entire roadmap
- Playwright migration is optional and only needed if Selenium causes container issues
- AWS deployment documentation should mirror Azure provisioning steps
