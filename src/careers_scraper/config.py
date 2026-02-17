"""Application configuration loaded from .env file."""

import os
from dotenv import load_dotenv

load_dotenv()


class Settings:
    """Application settings loaded from environment variables."""

    # Telegram
    telegram_bot_token: str = os.getenv("TELEGRAM_BOT_TOKEN", "")
    telegram_chat_id: str = os.getenv("TELEGRAM_CHAT_ID", "")

    # Scraping
    search_keywords: str = os.getenv("SEARCH_KEYWORDS", "python,backend,developer")
    scrape_interval: int = int(os.getenv("SCRAPE_INTERVAL", "60"))

    # App
    environment: str = os.getenv("ENVIRONMENT", "development")

    @property
    def keywords_list(self) -> list[str]:
        """Convert comma-separated keywords to lowercase list."""
        return [k.strip().lower() for k in self.search_keywords.split(",") if k.strip()]


settings = Settings()
