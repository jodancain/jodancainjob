"""High level orchestration for the airdrop summary service."""
from __future__ import annotations

from dataclasses import asdict
from datetime import datetime
from typing import List

from .airdrop_detector import AirdropDetector
from .config import Settings, get_settings
from .models import AirdropSummary, Tweet
from .summarizer import AirdropSummarizer
from .twitter_client import TwitterClient


class AirdropSummaryService:
    """Service responsible for refreshing and serving summaries."""

    def __init__(self, settings: Settings | None = None):
        self.settings = settings or get_settings()
        self.detector = AirdropDetector(self.settings.keywords)
        self.twitter_client = TwitterClient(self.settings)
        self.summarizer = AirdropSummarizer(self.detector)
        self._cache: AirdropSummary | None = None
        self._last_updated: datetime | None = None

    def refresh(self) -> AirdropSummary:
        """Fetch new data and refresh the in-memory cache."""

        tweets = self._fetch_tweets()
        airdrop_tweets = [tweet for tweet in tweets if self.detector.is_airdrop_tweet(tweet)]
        summary = self.summarizer.summarize(airdrop_tweets)
        self._cache = summary
        self._last_updated = datetime.utcnow()
        return summary

    def get_summary(self, force_refresh: bool = False) -> dict:
        """Return the latest summary, refreshing it if required."""

        if force_refresh or self._cache is None:
            summary = self.refresh()
        else:
            summary = self._cache
        generated_at = self._last_updated.isoformat() if self._last_updated else None
        return {
            "generated_at": generated_at,
            "summary": asdict(summary),
        }

    # ------------------------------------------------------------------
    def _fetch_tweets(self) -> List[Tweet]:
        handles = self.settings.tracked_handles
        return self.twitter_client.fetch_recent_tweets(handles, self.settings.max_results_per_handle)
