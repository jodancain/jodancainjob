"""Entry point for running the FastAPI service."""
from __future__ import annotations

from dataclasses import asdict

from fastapi import Depends, FastAPI

from app.config import Settings, get_settings
from app.service import AirdropSummaryService

app = FastAPI(
    title="2Web3 KOL Airdrop Activity Summary",
    description=(
        "Summarise airdrop-related campaigns posted by tracked Web3 KOLs on X."
    ),
    version="0.1.0",
)


def get_service(settings: Settings = Depends(get_settings)) -> AirdropSummaryService:
    return AirdropSummaryService(settings=settings)


@app.get("/health", tags=["system"])
def healthcheck() -> dict:
    return {"status": "ok"}


@app.get("/summaries", tags=["summaries"])
def read_summary(force_refresh: bool = False, service: AirdropSummaryService = Depends(get_service)) -> dict:
    """Return the latest computed summary."""

    return service.get_summary(force_refresh=force_refresh)


@app.post("/summaries/refresh", tags=["summaries"], status_code=202)
def refresh_summary(service: AirdropSummaryService = Depends(get_service)) -> dict:
    """Force a refresh of the cached summary."""

    summary = service.refresh()
    return {
        "generated_at": service._last_updated.isoformat() if service._last_updated else None,
        "summary": asdict(summary),
    }
