"""Application configuration loaded from config.yaml."""

import yaml
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent.parent / "config.yaml"


@dataclass
class VacancyConfig:
    name: str
    url: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    vacancies: list[VacancyConfig]
    scrape_interval: int = 60
    environment: str = "development"


def _load() -> Settings:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    vacancies = [
        VacancyConfig(
            name=v["name"],
            url=v["url"],
            keywords=[kw.lower() for kw in v.get("keywords", [])],
        )
        for v in data.get("vacancies", [])
    ]

    return Settings(
        telegram_bot_token=str(data.get("telegram_bot_token", "")),
        telegram_chat_id=str(data.get("telegram_chat_id", "")),
        vacancies=vacancies,
        scrape_interval=int(data.get("scrape_interval", 60)),
        environment=str(data.get("environment", "development")),
    )


settings = _load()
