"""Application configuration loaded from config.yaml."""

import os
import yaml
from dataclasses import dataclass, field
from pathlib import Path

CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"


@dataclass
class VacancyConfig:
    name: str
    url: str
    keywords: list[str] = field(default_factory=list)


@dataclass
class LogRotationConfig:
    max_bytes: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5


@dataclass
class Settings:
    telegram_bot_token: str
    telegram_chat_id: str
    vacancies: list[VacancyConfig]
    environment: str = "development"
    dedup_seen_urls: bool = True
    log_rotation: LogRotationConfig = field(default_factory=LogRotationConfig)


def _load() -> Settings:
    if not CONFIG_PATH.exists():
        raise FileNotFoundError(f"Config file not found: {CONFIG_PATH}")

    with open(CONFIG_PATH, "r", encoding="utf-8") as f:
        data = yaml.safe_load(f)

    token = os.environ.get("TELEGRAM_BOT_TOKEN") or str(data.get("telegram_bot_token", ""))
    chat_id = os.environ.get("TELEGRAM_CHAT_ID") or str(data.get("telegram_chat_id", ""))

    vacancies = [
        VacancyConfig(
            name=v["name"],
            url=v["url"],
            keywords=[kw.lower() for kw in v.get("keywords", [])],
        )
        for v in data.get("vacancies", [])
    ]

    rot = data.get("log_rotation", {}) or {}
    log_rotation = LogRotationConfig(
        max_bytes=int(rot.get("max_bytes", 10 * 1024 * 1024)),
        backup_count=int(rot.get("backup_count", 5)),
    )

    return Settings(
        telegram_bot_token=token,
        telegram_chat_id=chat_id,
        vacancies=vacancies,
        environment=str(data.get("environment", "development")),
        dedup_seen_urls=bool(data.get("dedup_seen_urls", True)),
        log_rotation=log_rotation,
    )


settings = _load()
