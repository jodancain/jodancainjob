"""Utilities for creating human-friendly summaries."""
from __future__ import annotations

from collections import defaultdict
from typing import Dict, Iterable, List

from .airdrop_detector import AirdropDetector
from .models import AirdropSummary, Tweet


class AirdropSummarizer:
    """Produce aggregated summaries for airdrop related tweets."""

    def __init__(self, detector: AirdropDetector, highlight_count: int = 3):
        self.detector = detector
        self.highlight_count = highlight_count

    def summarize(self, tweets: Iterable[Tweet]) -> AirdropSummary:
        tweets_list = sorted(tweets, key=lambda tweet: tweet.created_at, reverse=True)
        total_mentions = len(tweets_list)
        keyword_counts = self.detector.aggregate_keyword_counts(tweets_list)

        grouped: Dict[str, List[Tweet]] = defaultdict(list)
        for tweet in tweets_list:
            grouped[tweet.author_handle].append(tweet)

        kol_breakdown = []
        for handle, handle_tweets in grouped.items():
            kol_breakdown.append(
                {
                    "handle": handle,
                    "mention_count": len(handle_tweets),
                    "latest_mentions": [self._tweet_to_dict(tweet) for tweet in handle_tweets[: self.highlight_count]],
                    "top_keywords": self._top_keywords(handle_tweets, limit=5),
                }
            )
        kol_breakdown.sort(key=lambda entry: entry["mention_count"], reverse=True)

        latest_mentions = [self._tweet_to_dict(tweet) for tweet in tweets_list[: self.highlight_count]]
        trending_keywords = [keyword for keyword, _ in keyword_counts.most_common(10)]

        return AirdropSummary(
            total_mentions=total_mentions,
            kol_breakdown=kol_breakdown,
            trending_keywords=trending_keywords,
            latest_mentions=latest_mentions,
        )

    # ------------------------------------------------------------------
    def _top_keywords(self, tweets: Iterable[Tweet], limit: int = 5) -> List[str]:
        counter = self.detector.aggregate_keyword_counts(tweets)
        return [keyword for keyword, _ in counter.most_common(limit)]

    @staticmethod
    def _tweet_to_dict(tweet: Tweet) -> dict:
        return {
            "id": tweet.id,
            "author_handle": tweet.author_handle,
            "created_at": tweet.created_at.isoformat(),
            "text": tweet.text,
            "url": tweet.url,
        }
