import asyncio
from telegram import Bot
from telegram.error import TelegramError
from config import settings
from typing import Dict


class TelegramNotifier:
    """Handle Telegram notifications for new job postings"""

    def __init__(self):
        self.bot_token = settings.telegram_bot_token
        self.chat_id = settings.telegram_chat_id
        self.bot = None

        if self.bot_token:
            self.bot = Bot(token=self.bot_token)

    async def send_job_notification(self, job: Dict):
        """Send notification about a new job posting"""
        if not self.bot or not self.chat_id:
            print("Telegram bot not configured. Skipping notification.")
            return

        message = self._format_job_message(job)

        try:
            await self.bot.send_message(
                chat_id=self.chat_id,
                text=message,
                parse_mode='HTML',
                disable_web_page_preview=False
            )
            print(f"Notification sent for job: {job.get('title', 'Unknown')}")
        except TelegramError as e:
            print(f"Error sending Telegram notification: {e}")

    def _format_job_message(self, job: Dict) -> str:
        """Format job information into a Telegram message"""
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
        """Synchronous wrapper for sending job notifications"""
        asyncio.run(self.send_job_notification(job))
