"""Telegram notification handler for job alerts."""

import html
import logging
import requests
from config import settings

logger = logging.getLogger(__name__)

_TELEGRAM_API_URL = "https://api.telegram.org/bot%s/sendMessage"

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

    def send_company_jobs(self, company: str, careers_url: str, jobs: list[dict]) -> None:
        """Send one message listing all matching jobs for a company."""
        if not self.bot_token or not self.chat_id:
            logger.warning("Telegram not configured. Skipping notification.")
            return

        message = self._format_company_message(company, careers_url, jobs)
        try:
            self._send(message)
            logger.info("Notification sent for %s (%d jobs)", company, len(jobs))
        except Exception as e:
            logger.error("Failed to send Telegram notification for %s: %s", company, e)

    def _format_company_message(self, company: str, careers_url: str, jobs: list[dict]) -> str:
        """Format all jobs for a company into a single HTML message."""
        _LIMIT = 4000

        color = _COMPANY_COLORS.get(company.lower(), "\u26aa") # ⚪ default
        count = len(jobs)
        job_word = "job" if count == 1 else "jobs"
        header = (
            f"{color}  <b>{html.escape(company)}</b> - <i>{count} new {job_word} found</i>\n"
            f"Careers page: {careers_url}\n"
        )

        entries = []
        for job in jobs:
            title = html.escape(job.get("title", "Untitled"))
            url = (job.get("url", "") or "").strip()

            if url:
                entry = f'\u2022 <a href="{url}">{title}</a>'
            else:
                entry = f"\u2022 {title}"

            entries.append(entry)

        # Enforce Telegram's 4096-char hard limit, with a small safety margin.
        base = header + "\n"
        kept = []
        for i, entry in enumerate(entries):
            candidate = base + "\n".join(kept + [entry])
            remaining = len(entries) - i - 1
            trailer = f"\n...and {remaining} more." if remaining else ""
            if len(candidate + trailer) > _LIMIT:
                kept.append(f"    ...and {len(entries) - i} more.")
                break
            kept.append(entry)

        return base + "\n".join(kept)

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
