"""Telegram notification handler for job alerts."""

import html
import logging
import time
import requests
from config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API_URL = "https://api.telegram.org/bot%s/sendMessage"
_LIMIT = 4000  # Telegram hard limit is 4096, small safety margin
_SEPARATOR = "──────────────"


class TelegramNotifier:
    """Handle Telegram notifications for new job postings."""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id

        if self.bot_token:
            logger.debug("Telegram notifier initialized")

    def send_cycle_summary(self, results: list[dict]) -> None:
        """Send one combined message with results from all companies."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured. Skipping notification.")
            return

        sections = [s for r in results if (s := self._format_section(r))]
        if not sections:
            return

        message = self._join_within_limit(sections)
        total_matches = sum(len(r["new_matches"]) for r in results)
        try:
            self._send(message)
            logger.info(
                "Cycle summary sent (%d new matches, %d companies)",
                total_matches, len(results),
            )
        except Exception as e:
            logger.error("Failed to send cycle summary: %s", e)

    def _format_section(self, result: dict) -> str | None:
        """Format one company's result into an HTML section.

        Returns None when there's nothing to report (matches exist but all
        already notified about — user already knows, no need to repeat).
        """
        company = result["company"]
        careers_url = result["url"]
        keywords = result["keywords"]
        new_matches = result["new_matches"]
        any_match = result["any_match"]
        total_jobs = result["total_jobs"]

        total_word = "job" if total_jobs == 1 else "jobs"
        kw_line = f"Keywords: <i>{html.escape(', '.join(keywords))}</i>" if keywords else ""

        if new_matches:
            count = len(new_matches)
            match_word = "match" if count == 1 else "matches"
            lines = [
                f"<b>{html.escape(company)}</b>",
                f"<b>{count} new {match_word}</b>  ·  {total_jobs} {total_word} on page",
            ]
            if kw_line:
                lines.append(kw_line)
            lines.append("")
            for job in new_matches:
                title = html.escape(job.get("title", "Untitled"))
                url = (job.get("url", "") or "").strip()
                lines.append(f'• <a href="{url}">{title}</a>' if url else f"• {title}")
            lines.append("")
            lines.append(f'<a href="{careers_url}">Careers page →</a>')
            return "\n".join(lines)

        if not any_match and total_jobs > 0:
            lines = [
                f"<b>{html.escape(company)}</b>",
                f"No matches  ·  {total_jobs} {total_word} on page",
            ]
            if kw_line:
                lines.append(kw_line)
            lines.append(f'<a href="{careers_url}">Careers page →</a>')
            return "\n".join(lines)

        return None  # any_match but all already notified — nothing new to say

    def _join_within_limit(self, sections: list[str]) -> str:
        """Join sections with a divider separator, truncating to fit the limit."""
        separator = f"\n{_SEPARATOR}\n"
        message = ""
        for i, section in enumerate(sections):
            candidate = message + (separator if message else "") + section
            if len(candidate) > _LIMIT:
                remaining = len(sections) - i
                message += f"\n{_SEPARATOR}\n...and {remaining} more section(s) truncated."
                break
            message = candidate
        return message

    def _send(self, message: str) -> None:
        """POST a message to the Telegram Bot API with retry on failure."""
        url = _TELEGRAM_API_URL % self.bot_token
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        for attempt in range(3):
            try:
                response = requests.post(url, json=payload, timeout=10)
                response.raise_for_status()
                return
            except Exception as e:
                if attempt == 2:
                    raise
                logger.warning("Telegram send failed (attempt %d/3): %s", attempt + 1, e)
                time.sleep(2 ** attempt)
