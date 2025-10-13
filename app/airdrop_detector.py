"""Utility functions to detect airdrop-related tweets."""
from __future__ import annotations

import re
from collections import Counter
from typing import Iterable, List

from .models import Tweet


class AirdropDetector:
    """Simple keyword-based detector for airdrop content."""

    def __init__(self, keywords: Iterable[str]):
        self.keywords = {keyword.lower() for keyword in keywords}
        # Precompile regex for performance and partial matching
        pattern = r"(" + "|".join(re.escape(keyword) for keyword in self.keywords) + r")"
        self._keyword_regex = re.compile(pattern, re.IGNORECASE)

    def is_airdrop_tweet(self, tweet: Tweet) -> bool:
        """Return True when the tweet mentions any tracked keyword."""

        return bool(self._keyword_regex.search(tweet.text))

    def extract_keywords(self, tweet: Tweet) -> List[str]:
        """Return the matched keywords for a tweet."""

        matches = self._keyword_regex.findall(tweet.text)
        return [match.lower() for match in matches]

    def aggregate_keyword_counts(self, tweets: Iterable[Tweet]) -> Counter[str]:
        """Compute keyword counts across the provided tweets."""

        counter: Counter[str] = Counter()
        for tweet in tweets:
            counter.update(self.extract_keywords(tweet))
        return counter
