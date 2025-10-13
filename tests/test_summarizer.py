from datetime import datetime

from app.airdrop_detector import AirdropDetector
from app.models import Tweet
from app.summarizer import AirdropSummarizer


def test_summarizer_groups_by_handle():
    detector = AirdropDetector(["airdrop", "drop"])
    summarizer = AirdropSummarizer(detector, highlight_count=2)
    tweets = [
        Tweet(
            id="1",
            author_handle="alice",
            created_at=datetime.fromisoformat("2024-03-15T10:00:00+00:00"),
            text="Great airdrop happening now!",
            url="https://example.com/1",
        ),
        Tweet(
            id="2",
            author_handle="alice",
            created_at=datetime.fromisoformat("2024-03-15T09:00:00+00:00"),
            text="Reminder about the drop tomorrow.",
            url="https://example.com/2",
        ),
        Tweet(
            id="3",
            author_handle="bob",
            created_at=datetime.fromisoformat("2024-03-14T08:00:00+00:00"),
            text="No drop here",
            url="https://example.com/3",
        ),
    ]

    summary = summarizer.summarize(tweets)

    assert summary.total_mentions == 3
    assert summary.kol_breakdown[0]["handle"] == "alice"
    assert summary.kol_breakdown[0]["mention_count"] == 2
    assert summary.latest_mentions[0]["id"] == "1"
