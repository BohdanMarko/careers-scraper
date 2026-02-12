"""Application configuration using Pydantic settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import List


class Settings(BaseSettings):
    """Application settings loaded from environment variables with CAREERS_ prefix."""

    model_config = SettingsConfigDict(
        env_prefix="CAREERS_",
        env_file=".env",
        case_sensitive=False,
        extra="ignore"
    )

    # Application settings
    environment: str = "development"
    debug: bool = False

    # Database settings
    database_url: str = "sqlite:///./careers.db"

    # Web server settings
    web_host: str = "0.0.0.0"
    web_port: int = 8000

    # Telegram settings
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""

    # Scraping settings
    search_keywords: str = "python,backend,developer"
    scrape_interval: int = 60  # minutes

    @property
    def keywords_list(self) -> List[str]:
        """Convert comma-separated keywords to list."""
        return [k.strip().lower() for k in self.search_keywords.split(",")]

    @property
    def engine_kwargs(self) -> dict:
        """Get database engine configuration based on database type."""
        if "sqlite" in self.database_url.lower():
            return {"connect_args": {"check_same_thread": False}}
        # PostgreSQL configuration for cloud deployment
        return {
            "pool_size": 5,
            "max_overflow": 10,
            "pool_pre_ping": True,
            "pool_recycle": 3600,
        }


# Global settings instance
settings = Settings()
