# Phase 1: Environment Variable Migration Guide

## Breaking Change: CAREERS_ Prefix Required

As part of Phase 1 restructuring, all environment variables now require the `CAREERS_` prefix.

## Variable Mapping

| Old Variable | New Variable | Default |
|--------------|--------------|---------|
| `TELEGRAM_BOT_TOKEN` | `CAREERS_TELEGRAM_BOT_TOKEN` | `""` |
| `TELEGRAM_CHAT_ID` | `CAREERS_TELEGRAM_CHAT_ID` | `""` |
| `SEARCH_KEYWORDS` | `CAREERS_SEARCH_KEYWORDS` | `"python,backend,developer"` |
| `DATABASE_URL` | `CAREERS_DATABASE_URL` | `"sqlite:///./careers.db"` |
| `WEB_HOST` | `CAREERS_WEB_HOST` | `"0.0.0.0"` |
| `WEB_PORT` | `CAREERS_WEB_PORT` | `8000` |
| `SCRAPE_INTERVAL` | `CAREERS_SCRAPE_INTERVAL` | `60` |

## Migration Steps

1. Backup: `cp .env .env.backup`
2. Copy template: `cp .env.example .env`
3. Update values with `CAREERS_` prefix
4. Verify: Test application startup

## Verification

```bash
python -c "from careers_scraper.config import settings; print(settings.database_url)"
```

See `.env.example` for complete template with all required variables.
