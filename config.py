from pydantic_settings import BaseSettings
from typing import List


class Settings(BaseSettings):
    telegram_bot_token: str = ""
    telegram_chat_id: str = ""
    search_keywords: str = "python,backend,developer"
    database_url: str = "sqlite:///./careers.db"
    web_host: str = "0.0.0.0"
    web_port: int = 8000
    scrape_interval: int = 60  # minutes

    class Config:
        env_file = ".env"
        case_sensitive = False

    @property
    def keywords_list(self) -> List[str]:
        """Convert comma-separated keywords to list"""
        return [k.strip().lower() for k in self.search_keywords.split(",")]


settings = Settings()
