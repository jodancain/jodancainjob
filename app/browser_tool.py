"""CLI helpers for running browser automation scenarios from JSON config files."""
from __future__ import annotations

import argparse
import json
import sys
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Iterable, Mapping, Optional, Sequence, TextIO

from .browser_automation import (
    BrowserAction,
    BrowserAutomation,
    BrowserAutomationResult,
)


@dataclass(slots=True)
class AutomationConfig:
    """Structured configuration for running :class:`BrowserAutomation`."""

    actions: list[BrowserAction]
    base_url: Optional[str] = None
    settings: dict[str, Any] = field(default_factory=dict)


def _ensure_mapping(data: Any, *, context: str) -> Mapping[str, Any]:
    if not isinstance(data, Mapping):
        raise ValueError(f"Expected a mapping for {context}")
    return data


def _ensure_sequence(data: Any, *, context: str) -> Sequence[Mapping[str, Any]]:
    if not isinstance(data, Sequence) or isinstance(data, (str, bytes, bytearray)):
        raise ValueError(f"Expected a sequence for {context}")
    return data  # type: ignore[return-value]


def load_config(path: Path) -> AutomationConfig:
    """Load a JSON configuration file into an :class:`AutomationConfig`."""

    content = path.read_text(encoding="utf-8")
    raw = json.loads(content)
    mapping = _ensure_mapping(raw, context="config root")

    base_url = mapping.get("base_url")
    if base_url is not None and not isinstance(base_url, str):
        raise ValueError("'base_url' must be a string when provided")

    raw_settings = mapping.get("settings")
    if raw_settings is None:
        settings: dict[str, Any] = {}
    else:
        settings = dict(_ensure_mapping(raw_settings, context="settings section"))

    raw_actions = mapping.get("actions")
    if raw_actions is None:
        raise ValueError("Config must define an 'actions' array")

    actions: list[BrowserAction] = []
    for index, raw_action in enumerate(_ensure_sequence(raw_actions, context="actions")):
        actions.append(BrowserAction.from_dict(_ensure_mapping(raw_action, context=f"action[{index}]")))

    return AutomationConfig(actions=actions, base_url=base_url, settings=settings)


def _format_result(result: BrowserAutomationResult) -> Iterable[str]:
    for action in result.actions:
        status = "ok" if action.success else "FAILED"
        detail = f" ({action.detail})" if action.detail else ""
        yield f"- {action.name}: {status}{detail}"


AutomationFactory = Callable[..., BrowserAutomation]


def run_from_config(
    path: Path,
    *,
    automation_factory: AutomationFactory = BrowserAutomation,
    stdout: TextIO,
    stderr: TextIO,
) -> int:
    """Load the config at *path* and execute the described actions."""

    try:
        config = load_config(path)
    except (OSError, ValueError) as exc:
        stderr.write(f"Failed to load automation config: {exc}\n")
        return 2

    automation = automation_factory(**config.settings)
    result = automation.run(config.actions, base_url=config.base_url)

    stdout.write(f"Ran {len(config.actions)} actions\n")
    for line in _format_result(result):
        stdout.write(f"{line}\n")

    return 0 if result.successful else 1


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Execute browser automation from a JSON config file")
    parser.add_argument("config", type=Path, help="Path to the JSON config file")
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = build_arg_parser()
    args = parser.parse_args(argv)
    return run_from_config(args.config, stdout=sys.stdout, stderr=sys.stderr)


if __name__ == "__main__":  # pragma: no cover - script entry point
    raise SystemExit(main())

