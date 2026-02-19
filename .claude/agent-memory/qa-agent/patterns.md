# QA Patterns — careers-scraper

## HTML Escaping Requirement (Telegram)

Telegram's HTML parse mode requires these characters escaped in text nodes:
- `&` -> `&amp;`
- `<` -> `&lt;`
- `>` -> `&gt;`

Inside href attribute values, `"` must be escaped as `&quot;`.

The minimum safe fix for `_format_company_message` is to apply `html.escape()` (stdlib) to
`title` and `department` before interpolation, and `html.escape(url, quote=True)` for the href.

Real-world trigger confirmed: job titles like "C++ & Rust Engineer" contain bare `&` which
causes Telegram to return 400 Bad Request.

## Keyword Match Invariant

Keywords enter the system through `config.py:_load()` which calls `.lower()` on each keyword.
`_matches_keywords` in `scraper_service.py` does NOT re-lowercase keywords — it depends on this
config invariant. If keywords are ever injected in tests or via a future API without going through
`_load()`, they will silently fail to match. Defensive fix: lowercase `kw` inside the `any()` call.

## Growe Selector Fallback Risk

`growe.py` tries selectors in order: `a[href*='/career/vacancy/']`, `[class*='vacancy']`, etc.
If `[class*='vacancy']` fires first and matches a container div:
- `get_attribute("href")` returns None
- url becomes `"https://growe.comNone"` (passes the `if not url` guard)
- Job is added to _seen_urls with garbage URL, permanently suppressed
- This is silent data loss

The first selector `a[href*='/career/vacancy/']` is the only reliable one for Growe's structure.

## Silent Data Loss Patterns

1. Scraper returns [] — logged as INFO "Found 0 jobs", indistinguishable from broken selector
2. Notification fails after URL is added to _seen_urls — job never notified, never retried
3. Telegram 400 on HTML injection — entire batch lost, only error in logs
4. Telegram message > 4096 chars — entire batch lost on first run with many jobs
5. CDProjektRed job with no id/slug and no applyUrl — url="" → silently skipped in _process_jobs, no log
6. Growe href=None → url="https://growe.com" → passes "not url" guard → contaminates _seen_urls

## Keyword Phrase Matching Gotcha

_matches_keywords uses `kw in text` (substring). Multi-word keywords like "middle php" require exact
word order adjacency in the concatenated field string. "PHP Developer (Middle)" will NOT match "middle php".
This is a config correctness issue the user must verify against live job titles.

## APScheduler Threading Note

APScheduler BackgroundScheduler runs jobs in daemon threads. The Selenium scrapers are
synchronous and blocking. Each scraping cycle can take 30-60+ seconds across 3 scrapers.
If scrape_interval is set to 1 minute and scrapers take >60s total, APScheduler will queue
overlapping jobs unless `max_instances=1` is set on the job. This is not currently set.
