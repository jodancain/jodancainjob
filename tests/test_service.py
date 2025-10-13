from app.config import Settings
from app.service import AirdropSummaryService


def test_service_refresh_uses_sample_data():
    settings = Settings(use_sample_data=True, tracked_handles=["2web3kol", "Web3Airdrops"])
    service = AirdropSummaryService(settings=settings)

    summary = service.refresh()

    assert summary.total_mentions > 0
    response = service.get_summary()
    assert response["summary"]["total_mentions"] == summary.total_mentions
    assert response["generated_at"] is not None
