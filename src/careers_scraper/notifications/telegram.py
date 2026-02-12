"""Telegram notification handler for job alerts."""

import logging
import asyncio
from telegram import Bot
from telegram.error import TelegramError
from careers_scraper.config import settings
from typing import Dict

logger = logging.getLogger(__name__)


class TelegramNotifier:
    """Handle Telegram notifications for new job postings."""

    def __init__(self):
        """Initialize Telegram bot with credentials from settings."""
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.bot = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)
            logger.debug("Telegram bot initialized")

    async def send_job_notification(self, job: Dict):
        """
        Send notification about a new job posting.

        Args:
            job: Dictionary containing job information
        """
        if not self.bot or not self.chat_id:
            logger.warning("Telegram bot not configured. Skipping notification.")
            return

        message = self._format_job_message(job)

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            logger.info(f"Notification sent for job: {job.get('title', 'Unknown')}")
        except TelegramError as e:
            logger.error(f"Error sending Telegram notification: {e}")

    def _format_job_message(self, job: Dict) -> str:
        """
        Format job information into a Telegram message.

        Args:
            job: Dictionary containing job information

        Returns:
            Formatted HTML message string
        """
        message = f"🔔 <b>New Job Match!</b>\n\n"
        message += f"<b>Company:</b> {job.get('company', 'N/A')}\n"
        message += f"<b>Position:</b> {job.get('title', 'N/A')}\n"

        if job.get('location'):
            message += f"<b>Location:</b> {job['location']}\n"

        if job.get('department'):
            message += f"<b>Department:</b> {job['department']}\n"

        if job.get('url'):
            message += f"\n<a href='{job['url']}'>View Job Posting</a>"

        return message

    def send_job_notification_sync(self, job: Dict):
        """
        Synchronous wrapper for sending job notifications.

        Args:
            job: Dictionary containing job information
        """
        asyncio.run(self.send_job_notification(job))
