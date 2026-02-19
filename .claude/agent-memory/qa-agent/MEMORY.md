# QA Agent Memory

## Architecture snapshot (verified 2026-02-19)

- 3 scrapers: Uklon (broken), CDProjektRed (JS extraction), Growe (Selenium multi-selector)
- Notification: direct requests.post to Telegram Bot API (no asyncio)
- Dedup: in-memory URL set (_seen_urls), resets on process restart
- Keywords: per-vacancy, lowercased at config load time in config.py _load()
- Scheduler: APScheduler BackgroundScheduler — NOT currently active (if True: guard in main.py bypasses it)

## Known live defects (as of 2026-02-19, updated after batching refactor review)

- `if True:` in `src/careers_scraper/main.py:17` — scheduler is dead code, app runs one cycle and exits
- Uklon scraper selectors are placeholders — returns [] silently, indistinguishable from zero postings
- HTML injection in telegram.py `_format_company_message` — title/department/url go into HTML string unescaped (html.escape not applied anywhere)
- Telegram message has no 4096-char length guard — batched notification can fail silently on first run; URLs already in _seen_urls so permanently suppressed
- Growe href=None produces url="https://growe.com" (not obviously garbage), passes _seen_urls guard, contaminates dedup set
- Double exception wrapping: send_company_jobs catches+logs, then re-raises; _process_jobs catches+logs again — two ERROR lines per failure
- CDProjektRed missing id+slug AND no applyUrl → apply_url="" → job silently skipped, no log entry
- cdprojektred.py uses f-string logging (not %s style) — inconsistent with rest of codebase
- Growe and CDProjektRed missing --window-size Chrome arg (Uklon has it)
- Growe zero-notification root cause: "middle php" keyword requires exact phrase substring match; "PHP Developer (Middle)" would NOT match — config issue, not code bug

## Confirmed correct patterns

- Keywords are lowercased in config.py; _matches_keywords lowercases the search text. Match is case-insensitive. BUT _matches_keywords does not lowercase keywords itself — relies on config.py invariant.
- _seen_urls is populated before keyword match — correct, prevents re-notification if keywords change
- driver.quit() in finally blocks — correct, no ChromeDriver leaks
- response.raise_for_status() called AFTER logging response.text — correct log capture order

## Recurring risk patterns in this codebase

- Bare `except:` in growe.py view_more click (line 45-46) — no logging at all
- Fixed time.sleep() for page load instead of WebDriverWait — all three scrapers
- Double exception wrapping: _process_jobs wraps send_company_jobs which already swallows internally
- _seen_urls grows unbounded — garbage URLs from Growe accumulate permanently

## See also

- `patterns.md` — detailed notes on keyword match invariants and HTML escaping requirements
