from __future__ import annotations

import io
import json
from pathlib import Path
from typing import Any

import pytest

from app.browser_automation import ActionResult, BrowserAutomationResult
from app.browser_tool import AutomationConfig, load_config, run_from_config


def write_config(tmp_path: Path, payload: dict[str, Any]) -> Path:
    path = tmp_path / "config.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_load_config_reads_actions_and_settings(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        {
            "base_url": "https://example.com",
            "settings": {"headless": False},
            "actions": [
                {"name": "goto", "url": "https://example.com/start"},
                {"name": "click", "selector": "text=Login"},
            ],
        },
    )

    config = load_config(path)

    assert isinstance(config, AutomationConfig)
    assert config.base_url == "https://example.com"
    assert config.settings == {"headless": False}
    assert [action.name for action in config.actions] == ["goto", "click"]


def test_load_config_rejects_invalid_action_name(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        {"actions": [{"name": "invalid"}]},
    )

    with pytest.raises(ValueError):
        load_config(path)


def test_run_from_config_reports_results(tmp_path: Path) -> None:
    path = write_config(
        tmp_path,
        {
            "settings": {"headless": True},
            "actions": [
                {"name": "goto", "url": "https://example.com"},
                {"name": "click", "selector": "text=Go"},
            ],
        },
    )

    captured: dict[str, Any] = {}

    class DummyAutomation:
        def __init__(self, **kwargs: Any) -> None:
            captured["kwargs"] = kwargs

        def run(self, actions: list[Any], *, base_url: str | None = None) -> BrowserAutomationResult:
            captured["actions"] = actions
            captured["base_url"] = base_url
            return BrowserAutomationResult(
                actions=[
                    ActionResult(name="goto", success=True),
                    ActionResult(name="click", success=False, detail="No element"),
                ]
            )

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_from_config(
        path,
        automation_factory=DummyAutomation,
        stdout=stdout,
        stderr=stderr,
    )

    assert exit_code == 1
    assert "Ran 2 actions" in stdout.getvalue()
    assert "click: FAILED" in stdout.getvalue()
    assert stderr.getvalue() == ""
    assert captured["kwargs"] == {"headless": True}
    assert [action.name for action in captured["actions"]] == ["goto", "click"]
    assert captured["base_url"] is None


def test_run_from_config_handles_invalid_payload(tmp_path: Path) -> None:
    invalid_path = tmp_path / "broken.json"
    invalid_path.write_text("not json", encoding="utf-8")

    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = run_from_config(invalid_path, stdout=stdout, stderr=stderr)

    assert exit_code == 2
    assert "Failed to load automation config" in stderr.getvalue()
