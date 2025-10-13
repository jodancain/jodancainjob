"""Data models for the airdrop summary service."""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import List


@dataclass(slots=True)
class Tweet:
    """Representation of a tweet fetched from X (Twitter)."""

    id: str
    author_handle: str
    created_at: datetime
    text: str
    url: str


@dataclass(slots=True)
class AirdropSummary:
    """Aggregate summary describing airdrop mentions for tracked accounts."""

    total_mentions: int
    kol_breakdown: List[dict]
    trending_keywords: List[str]
    latest_mentions: List[dict]
