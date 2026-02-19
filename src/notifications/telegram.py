"""Telegram notification handler for job alerts."""

import html
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API_URL = "https://api.telegram.org/bot%s/sendMessage"
_LIMIT = 4000  # Telegram hard limit is 4096, small safety margin

_COMPANY_COLORS = {
    "uklon": "\U0001f7e1",           # 🟡 yellow
    "cd projekt red": "\U0001f534",  # 🔴 red
    "growe": "\U0001f7e2"            # 🟢 green
}


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

        color = _COMPANY_COLORS.get(company.lower(), "\u26aa")
        kw_line = f"Keywords: <i>{html.escape(', '.join(keywords))}</i>\n" if keywords else ""

        if new_matches:
            count = len(new_matches)
            job_word = "job" if count == 1 else "jobs"
            header = (
                f"{color}  <b>{html.escape(company)}</b> - "
                f"<i>{count} new {job_word} found</i>\n"
                f"{kw_line}"
                f"Careers page: {careers_url}\n"
            )
            entries = []
            for job in new_matches:
                title = html.escape(job.get("title", "Untitled"))
                url = (job.get("url", "") or "").strip()
                entry = f'\u2022 <a href="{url}">{title}</a>' if url else f"\u2022 {title}"
                entries.append(entry)
            return header + "\n".join(entries)

        if not any_match and total_jobs > 0:
            job_word = "job" if total_jobs == 1 else "jobs"
            return (
                f"{color}  <b>{html.escape(company)}</b> - <i>no matching jobs</i>\n"
                f"{kw_line}"
                f"{total_jobs} {job_word} on page, none match your keywords.\n"
                f"Careers page: {careers_url}"
            )

        return None  # any_match but all already notified — nothing new to say

    def _join_within_limit(self, sections: list[str]) -> str:
        """Join sections with a blank line separator, truncating to fit the limit."""
        separator = "\n\n"
        message = ""
        for i, section in enumerate(sections):
            candidate = message + (separator if message else "") + section
            if len(candidate) > _LIMIT:
                remaining = len(sections) - i
                message += f"\n\n...and {remaining} more section(s) truncated."
                break
            message = candidate
        return message

    def _send(self, message: str) -> None:
        """POST a message to the Telegram Bot API."""
        url = _TELEGRAM_API_URL % self.bot_token
        payload = {
            "chat_id": self.chat_id,
            "text": message,
            "parse_mode": "HTML",
            "disable_web_page_preview": True,
        }
        response = requests.post(url, json=payload, timeout=10)
        response.raise_for_status()
