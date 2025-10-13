"""Client responsible for retrieving tweets from X (Twitter)."""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, List, Sequence

try:  # pragma: no cover - optional dependency import
    import requests
    from requests import Response, Session
except ImportError:  # pragma: no cover
    requests = None
    Response = Any  # type: ignore[assignment]
    Session = Any  # type: ignore[assignment]

from .config import Settings
from .models import Tweet

logger = logging.getLogger(__name__)


@dataclass(slots=True)
class TwitterClient:
    """Lightweight wrapper around the Twitter/X API v2."""

    settings: Settings
    session: Session | None = None

    def __post_init__(self) -> None:
        if self.session is None and requests is not None:
            self.session = requests.Session()

    def fetch_recent_tweets(
        self, handles: Sequence[str], max_results_per_handle: int | None = None
    ) -> List[Tweet]:
        """Fetch recent tweets for the provided handles.

        When the application is configured to use sample data (or a bearer token is
        not supplied) the method will read from the JSON fixture bundled with the
        project. Otherwise, it will attempt to query the official API.
        """

        max_results = max_results_per_handle or self.settings.max_results_per_handle

        if self.settings.use_sample_data or not self.settings.twitter_bearer_token:
            logger.info("Loading tweets from sample dataset.")
            return self._load_sample_data(handles, max_results)

        if requests is None:
            raise RuntimeError(
                "The 'requests' package is required for live API calls. Install it or enable sample data."
            )

        tweets: List[Tweet] = []
        for handle in handles:
            try:
                user_id = self._resolve_user_id(handle)
                tweets.extend(self._fetch_user_tweets(user_id, handle, max_results))
            except requests.HTTPError as exc:
                logger.warning("Failed to fetch tweets for %s: %s", handle, exc)
        return tweets

    # ------------------------------------------------------------------
    # Sample data helpers
    # ------------------------------------------------------------------
    def _load_sample_data(self, handles: Sequence[str], max_results: int) -> List[Tweet]:
        sample_path = Path(self.settings.sample_data_path)
        if not sample_path.exists():
            raise FileNotFoundError(
                f"Sample data file not found at {sample_path.resolve()!s}."
            )
        with sample_path.open("r", encoding="utf-8") as fp:
            payload = json.load(fp)

        tweets: List[Tweet] = []
        allowed_handles = {handle.lower().lstrip("@") for handle in handles}
        for raw in payload.get("data", []):
            handle = raw.get("author_handle", "")
            if allowed_handles and handle.lower() not in allowed_handles:
                continue
            tweets.append(
                Tweet(
                    id=str(raw["id"]),
                    author_handle=handle,
                    created_at=self._parse_datetime(raw["created_at"]),
                    text=raw.get("text", ""),
                    url=raw.get("url", ""),
                )
            )
        tweets.sort(key=lambda tweet: tweet.created_at, reverse=True)
        return tweets[: len(handles) * max_results if handles else max_results]

    # ------------------------------------------------------------------
    # API helpers
    # ------------------------------------------------------------------
    def _resolve_user_id(self, handle: str) -> str:
        url = f"https://api.twitter.com/2/users/by/username/{handle}"
        response = self._request(url)
        data = response.json()
        return data["data"]["id"]

    def _fetch_user_tweets(self, user_id: str, handle: str, max_results: int) -> List[Tweet]:
        url = f"https://api.twitter.com/2/users/{user_id}/tweets"
        params = {
            "max_results": min(max_results, 100),
            "tweet.fields": "created_at",
            "exclude": "replies,retweets",
        }
        response = self._request(url, params=params)
        data = response.json()
        tweets: List[Tweet] = []
        for item in data.get("data", []):
            tweets.append(
                Tweet(
                    id=item["id"],
                    author_handle=handle,
                    created_at=self._parse_datetime(item["created_at"]),
                    text=item.get("text", ""),
                    url=f"https://twitter.com/{handle}/status/{item['id']}",
                )
            )
        return tweets

    def _request(self, url: str, params: dict | None = None) -> Response:
        if requests is None or self.session is None:
            raise RuntimeError(
                "The 'requests' package is required for live API calls. Install it or enable sample data."
            )
        headers = {
            "Authorization": f"Bearer {self.settings.twitter_bearer_token}",
        }
        response = self.session.get(url, headers=headers, params=params, timeout=15)
        response.raise_for_status()
        return response

    @staticmethod
    def _parse_datetime(value: str) -> datetime:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
