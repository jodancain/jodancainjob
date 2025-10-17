from __future__ import annotations

from contextlib import contextmanager
from dataclasses import dataclass
from typing import Any, Iterator

from app.browser_automation import ActionResult, BrowserAction, BrowserAutomation


@dataclass
class FakePage:
    calls: list[tuple[str, tuple[Any, ...], dict[str, Any]]]

    def goto(self, url: str, **options: Any) -> None:
        self.calls.append(("goto", (url,), options))

    def click(self, selector: str, **options: Any) -> None:
        self.calls.append(("click", (selector,), options))

    def fill(self, selector: str, text: str, **options: Any) -> None:
        self.calls.append(("fill", (selector, text), options))

    def wait_for_selector(self, selector: str, **options: Any) -> None:
        self.calls.append(("wait_for_selector", (selector,), options))

    def screenshot(self, *, path: str, **options: Any) -> None:
        self.calls.append(("screenshot", (path,), options))


@dataclass
class FakeContext:
    page: FakePage
    closed: bool = False

    def new_page(self) -> FakePage:
        return self.page

    def close(self) -> None:
        self.closed = True


@dataclass
class FakeBrowser:
    context: FakeContext
    closed: bool = False

    def new_context(self, **_: Any) -> FakeContext:
        return self.context

    def close(self) -> None:
        self.closed = True


@dataclass
class FakeBrowserType:
    browser: FakeBrowser
    launch_kwargs: dict[str, Any] | None = None

    def launch(self, **kwargs: Any) -> FakeBrowser:
        self.launch_kwargs = kwargs
        return self.browser


@dataclass
class FakePlaywright:
    chromium: FakeBrowserType


def make_factory() -> tuple[callable[[], Iterator[FakePlaywright]], FakePage, FakeBrowserType]:
    page = FakePage(calls=[])
    context = FakeContext(page=page)
    browser = FakeBrowser(context=context)
    browser_type = FakeBrowserType(browser=browser)

    @contextmanager
    def factory() -> Iterator[FakePlaywright]:
        yield FakePlaywright(chromium=browser_type)

    return factory, page, browser_type


def test_browser_automation_runs_steps_in_order() -> None:
    factory, page, browser_type = make_factory()
    automation = BrowserAutomation(headless=False, playwright_factory=factory)

    actions = [
        BrowserAction(name="goto", url="https://example.com", options={"wait_until": "networkidle"}),
        BrowserAction(name="click", selector="text=Login"),
        BrowserAction(name="fill", selector="#username", text="user"),
        BrowserAction(name="wait_for_selector", selector="#result"),
        BrowserAction(name="screenshot", path="result.png"),
    ]

    result = automation.run(actions)

    assert result.successful
    assert [call[0] for call in page.calls] == [
        "goto",
        "click",
        "fill",
        "wait_for_selector",
        "screenshot",
    ]
    assert browser_type.launch_kwargs == {"headless": False}


def test_browser_automation_stops_after_failure_when_configured() -> None:
    factory, page, _ = make_factory()
    automation = BrowserAutomation(playwright_factory=factory)

    actions = [
        BrowserAction(name="click"),
        BrowserAction(name="goto", url="https://example.com"),
    ]

    result = automation.run(actions)

    assert not result.successful
    assert len(result.actions) == 1
    assert isinstance(result.actions[0], ActionResult)
    assert page.calls == []


def test_browser_automation_continues_on_failure_when_requested() -> None:
    factory, page, _ = make_factory()
    automation = BrowserAutomation(stop_on_failure=False, playwright_factory=factory)

    actions = [
        BrowserAction(name="click"),
        BrowserAction(name="goto", url="https://example.com"),
        BrowserAction(name="fill", selector="#query", text="airdrop"),
    ]

    result = automation.run(actions)

    assert not result.successful
    assert len(result.actions) == 3
    assert [call[0] for call in page.calls] == ["goto", "fill"]


def test_browser_automation_resolves_base_url_paths() -> None:
    factory, page, _ = make_factory()
    automation = BrowserAutomation(playwright_factory=factory)

    actions = [
        BrowserAction(name="goto", path="/path"),
    ]

    result = automation.run(actions, base_url="https://example.com")

    assert result.successful
    assert page.calls[0][1][0] == "https://example.com/path"


def test_browser_automation_requires_url_for_goto() -> None:
    factory, _, _ = make_factory()
    automation = BrowserAutomation(playwright_factory=factory)

    actions = [BrowserAction(name="goto")]

    result = automation.run(actions)

    assert not result.successful
    assert result.actions[0].detail is not None
