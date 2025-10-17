"""Utility for automating browser actions with Playwright."""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, ContextManager, List, Literal, Mapping, Optional, Sequence
from urllib.parse import urljoin

try:  # pragma: no cover - import guard executed once
    from playwright.sync_api import sync_playwright
except Exception:  # pragma: no cover - handled lazily
    sync_playwright = None  # type: ignore[assignment]


BrowserActionName = Literal[
    "goto",
    "click",
    "fill",
    "wait_for_selector",
    "screenshot",
]


SUPPORTED_ACTIONS: Sequence[BrowserActionName] = (
    "goto",
    "click",
    "fill",
    "wait_for_selector",
    "screenshot",
)


@dataclass(slots=True)
class BrowserAction:
    """Description of a single browser automation step."""

    name: BrowserActionName
    selector: Optional[str] = None
    text: Optional[str] = None
    url: Optional[str] = None
    path: Optional[str] = None
    options: Optional[dict[str, Any]] = None

    @classmethod
    def from_dict(cls, data: Mapping[str, Any]) -> "BrowserAction":
        """Build an action from a JSON-style mapping.

        The method provides a lightweight bridge between static configuration files and
        the strongly-typed ``BrowserAction`` dataclass used by the automation runtime.
        Only keys that map to existing dataclass fields are consumed; additional keys
        are ignored to keep the loader tolerant of metadata that callers may persist in
        their config files.
        """

        try:
            name = data["name"]
        except KeyError as exc:  # pragma: no cover - validated in tests
            raise ValueError("Action definition requires a 'name'") from exc

        if name not in SUPPORTED_ACTIONS:  # type: ignore[arg-type]
            raise ValueError(f"Unsupported action name: {name!r}")

        def optional_str(key: str) -> Optional[str]:
            value = data.get(key)
            if value is None:
                return None
            if not isinstance(value, str):
                raise ValueError(f"'{key}' must be a string when provided")
            return value

        options = data.get("options")
        if options is not None and not isinstance(options, Mapping):
            raise ValueError("'options' must be a mapping when provided")

        return cls(
            name=name,
            selector=optional_str("selector"),
            text=optional_str("text"),
            url=optional_str("url"),
            path=optional_str("path"),
            options=dict(options) if options is not None else None,
        )


@dataclass(slots=True)
class ActionResult:
    """Result for a single executed browser action."""

    name: BrowserActionName
    success: bool
    detail: Optional[str] = None


@dataclass(slots=True)
class BrowserAutomationResult:
    """Aggregated result of executing a set of browser actions."""

    actions: List[ActionResult]

    @property
    def successful(self) -> bool:
        """Return ``True`` when all actions were executed successfully."""

        return all(result.success for result in self.actions)


PlaywrightFactory = Callable[[], ContextManager[Any]]


class BrowserAutomation:
    """Run a sequence of browser actions using Playwright."""

    def __init__(
        self,
        *,
        browser_type: str = "chromium",
        headless: bool = True,
        launch_options: Optional[dict[str, Any]] = None,
        context_options: Optional[dict[str, Any]] = None,
        stop_on_failure: bool = True,
        playwright_factory: Optional[PlaywrightFactory] = None,
    ) -> None:
        self.browser_type = browser_type
        self.headless = headless
        self.launch_options = dict(launch_options or {})
        self.context_options = dict(context_options or {})
        self.stop_on_failure = stop_on_failure
        if playwright_factory is not None:
            self._playwright_factory = playwright_factory
        else:
            if sync_playwright is None:  # pragma: no cover - runtime guard
                raise RuntimeError(
                    "Playwright is not installed. Install the 'playwright' package "
                    "or provide a custom playwright_factory."
                )
            self._playwright_factory = sync_playwright

    _SUPPORTED_ACTIONS: Sequence[BrowserActionName] = SUPPORTED_ACTIONS

    # ------------------------------------------------------------------
    def run(
        self,
        actions: Sequence[BrowserAction],
        *,
        base_url: Optional[str] = None,
    ) -> BrowserAutomationResult:
        """Execute the provided actions sequentially and return the result."""

        executed: List[ActionResult] = []
        with self._playwright_factory() as playwright:
            browser_type = self._get_browser_type(playwright)
            browser = browser_type.launch(headless=self.headless, **self.launch_options)
            try:
                context = browser.new_context(**self.context_options)
                try:
                    page = context.new_page()
                    for action in actions:
                        result = self._execute_action(page, action, base_url)
                        executed.append(result)
                        if not result.success and self.stop_on_failure:
                            break
                finally:
                    context.close()
            finally:
                browser.close()
        return BrowserAutomationResult(executed)

    # ------------------------------------------------------------------
    def _get_browser_type(self, playwright: Any) -> Any:
        browser_type = getattr(playwright, self.browser_type, None)
        if browser_type is None:
            raise ValueError(f"Browser type '{self.browser_type}' is not available")
        return browser_type

    # ------------------------------------------------------------------
    def _execute_action(
        self,
        page: Any,
        action: BrowserAction,
        base_url: Optional[str],
    ) -> ActionResult:
        try:
            handler = getattr(self, f"_handle_{action.name}")
        except AttributeError as exc:  # pragma: no cover - guarded by type hints
            return ActionResult(action.name, False, detail=str(exc))

        try:
            handler(page, action, base_url)
        except Exception as exc:  # noqa: BLE001
            return ActionResult(action.name, False, detail=str(exc))
        return ActionResult(action.name, True)

    # ------------------------------------------------------------------
    def _handle_goto(self, page: Any, action: BrowserAction, base_url: Optional[str]) -> None:
        url = self._resolve_url(action, base_url)
        options = dict(action.options or {})
        page.goto(url, **options)

    def _handle_click(self, page: Any, action: BrowserAction, base_url: Optional[str]) -> None:  # noqa: ARG002
        if not action.selector:
            raise ValueError("'click' action requires a selector")
        options = dict(action.options or {})
        page.click(action.selector, **options)

    def _handle_fill(self, page: Any, action: BrowserAction, base_url: Optional[str]) -> None:  # noqa: ARG002
        if not action.selector:
            raise ValueError("'fill' action requires a selector")
        if action.text is None:
            raise ValueError("'fill' action requires text to input")
        options = dict(action.options or {})
        page.fill(action.selector, action.text, **options)

    def _handle_wait_for_selector(
        self,
        page: Any,
        action: BrowserAction,
        base_url: Optional[str],
    ) -> None:  # noqa: ARG002
        if not action.selector:
            raise ValueError("'wait_for_selector' action requires a selector")
        options = dict(action.options or {})
        page.wait_for_selector(action.selector, **options)

    def _handle_screenshot(self, page: Any, action: BrowserAction, base_url: Optional[str]) -> None:  # noqa: ARG002
        if not action.path:
            raise ValueError("'screenshot' action requires a path")
        options = dict(action.options or {})
        page.screenshot(path=action.path, **options)

    # ------------------------------------------------------------------
    def _resolve_url(self, action: BrowserAction, base_url: Optional[str]) -> str:
        if action.url:
            return action.url
        if action.path and base_url:
            return urljoin(base_url.rstrip("/") + "/", action.path.lstrip("/"))
        if base_url and not action.path:
            return base_url
        raise ValueError("No URL provided for 'goto' action")
