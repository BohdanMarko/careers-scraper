# Python Expert Agent Memory

## Project: careers-scraper

### Key conventions confirmed

- Logging: always `%`-style format strings, never f-strings in log calls
- No new dependencies — stdlib (`html`, etc.) is always preferred
- Type hints on new code only; leave existing signatures untouched
- `list[dict]` (lowercase) used for job lists throughout (Python 3.9+ style)

### Architectural landmarks

- `src/careers_scraper/notifications/telegram.py` — Telegram notifier; HTML parse_mode
- `src/careers_scraper/scrapers/implementations/growe.py` — Selenium scraper; multi-selector fallback
- Job dict keys: title, url, location, department, description, posted_date

### Patterns and pitfalls

- Telegram HTML mode: escape all user-supplied values with `html.escape()`; URLs go in href unescaped but `.strip()`-ed
- Telegram 4096-char limit: build incrementally, append "...and N more." trailer before exceeding 4000 chars
- `_send()` should only call `raise_for_status()`; the caller (`send_company_jobs`) owns the single error log
- Growe URL guard: after constructing the URL, check `"/career/vacancy/" in url` before adding to seen set
- Bare `except:` is a PEP 8 violation — always use `except Exception:` at minimum

### See also

- `patterns.md` — (create if needed for deeper pattern notes)
