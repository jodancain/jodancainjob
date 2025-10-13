"""Application configuration utilities."""
from __future__ import annotations

import os
import os

from dataclasses import dataclass, field
from functools import lru_cache
from pathlib import Path
from typing import List


def _load_dotenv() -> None:
    env_path = Path(".env")
    if not env_path.exists():
        return
    for line in env_path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        key, value = line.split("=", 1)
        os.environ.setdefault(key.strip(), value.strip())


_load_dotenv()


def _split_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip().lstrip("@") for item in value.split(",") if item.strip()]


def _to_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    return value.strip().lower() in {"1", "true", "yes", "on"}


def _to_int(value: str | None, default: int) -> int:
    if value is None:
        return default
    try:
        return int(value)
    except ValueError:
        return default


@dataclass(slots=True)
class Settings:
    twitter_bearer_token: str | None = None
    tracked_handles: List[str] = field(default_factory=lambda: ["2web3kol", "Web3Airdrops"])
    keywords: List[str] = field(
        default_factory=lambda: [
            "airdrop",
            "空投",
            "giveaway",
            "drop",
            "campaign",
            "whitelist",
            "mint",
            "reward",
        ]
    )
    max_results_per_handle: int = 25
    use_sample_data: bool = False
    sample_data_path: Path = Path("data/sample_tweets.json")

    def __post_init__(self) -> None:
        self.tracked_handles = [handle.lstrip("@") for handle in self.tracked_handles]
        self.keywords = [keyword for keyword in self.keywords if keyword]
        if not isinstance(self.sample_data_path, Path):
            self.sample_data_path = Path(self.sample_data_path)

    @classmethod
    def from_env(cls) -> "Settings":
        data = {}
        token = os.getenv("TWITTER_BEARER_TOKEN")
        if token:
            data["twitter_bearer_token"] = token

        handles = _split_csv(os.getenv("TRACKED_HANDLES"))
        if handles:
            data["tracked_handles"] = handles

        keywords = _split_csv(os.getenv("AIRDROP_KEYWORDS"))
        if keywords:
            data["keywords"] = keywords

        use_sample = _to_bool(os.getenv("USE_SAMPLE_DATA"))
        data["use_sample_data"] = use_sample

        max_results = _to_int(os.getenv("MAX_RESULTS_PER_HANDLE"), default=25)
        data["max_results_per_handle"] = max_results

        sample_path = os.getenv("SAMPLE_DATA_PATH")
        if sample_path:
            data["sample_data_path"] = Path(sample_path)

        return cls(**data)


@lru_cache()
def get_settings() -> Settings:
    return Settings.from_env()
