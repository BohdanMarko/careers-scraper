# Python Expert Agent Memory

## Project: careers-scraper

### Key conventions confirmed

- Logging: always `%`-style format strings, never f-strings in log calls
- No new dependencies — stdlib (`html`, `threading`, `concurrent.futures`, etc.) always preferred
- Type hints on new code only; leave existing signatures untouched
- `list[dict]` (lowercase) used for job lists throughout (Python 3.9+ style)

### Architectural landmarks

- `src/scrapers/base.py` — `create_chrome_driver()` sets 30s page load timeout + `implicitly_wait(0)`; `BaseScraper` ABC has only `scrape()` abstract method
- `src/services/scraper_service.py` — parallel scraping via `ThreadPoolExecutor`; `_seen_urls` capped at 10k (trims to 5k); `_matches_keywords()` lives here only
- `src/notifications/telegram.py` — HTML parse_mode; `_send()` retries 3x with exponential backoff (1s, 2s)
- `src/scrapers/implementations/growe.py` — smart VIEW MORE loop waits for DOM count change; silent exception → `logger.debug`
- `src/scrapers/implementations/uklon.py` — waits for `div.w-grid__item-panel` via `WebDriverWait` before scroll
- `src/scrapers/implementations/cdprojektred.py` — waits for `window.cdpData.jobsData !== null` via `WebDriverWait` lambda
- `main.py` — scheduler keep-alive uses `threading.Event().wait()`, not `time.sleep()` loop
- Job dict keys: title, url, location, department, description, posted_date

### Patterns and pitfalls

- Telegram HTML mode: escape all user-supplied values with `html.escape()`; URLs go in href unescaped but `.strip()`-ed
- Telegram 4096-char limit: build incrementally, append "...and N more." trailer before exceeding 4000 chars
- `_send()` retries on any exception; caller (`send_cycle_summary`) owns the single error log on final failure
- Growe URL guard: check `"/career/vacancy/" in url` before appending job
- Bare `except:` is a PEP 8 violation — always use `except Exception as e:` when logging
- WebDriverWait lambda default arg capture: `lambda d, pc=prev_count: ...` avoids late-binding closure bug
- `implicitly_wait(0)` must be set when using explicit `WebDriverWait` — mixing the two causes unexpected delays
- Flat `src/` layout — imports are `from scrapers.base import ...`, NOT `from careers_scraper.scrapers...`

### See also

- `patterns.md` — (create if needed for deeper pattern notes)
