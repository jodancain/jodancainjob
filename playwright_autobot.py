# playwright_autobot.py
"""
A small, config-driven Playwright automation runner (sync API).

Features
- Persistent user data dir (reuses login cookies/localStorage)
- Config-driven steps (goto, wait, click, fill, press, screenshot, sleep)
- CLI flags to override headless, profile path, timeouts and browser type
- Simple retries per-step and global default timeout

Usage
1) pip install playwright
   python -m playwright install
2) python playwright_autobot.py --config example_config.jsonc
   # or specify your own: --profile ./profile --headless 0 --browser chromium

Config (JSON or JSONC) example in example_config.jsonc
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

from playwright.sync_api import sync_playwright, TimeoutError as PWTimeout

# ------------------------------- utils -------------------------------

def load_json_or_jsonc(path: Path) -> Dict[str, Any]:
    text = path.read_text(encoding="utf-8")
    # strip // and /* */ comments for JSONC
    text = re.sub(r"//.*?$", "", text, flags=re.MULTILINE)
    text = re.sub(r"/\*.*?\*/", "", text, flags=re.DOTALL)
    return json.loads(text)

def str2bool(v: str) -> bool:
    return str(v).lower() in {"1", "true", "yes", "y", "on"}

def log(level: str, msg: str, ctx: Optional[Dict[str, Any]] = None) -> None:
    if ctx:
        kv = " ".join(f"{k}={v}" for k, v in ctx.items())
        print(f"[{level.upper()}] {msg} | {kv}")
    else:
        print(f"[{level.upper()}] {msg}")

# ------------------------------ config -------------------------------

@dataclass
class Step:
    action: str
    selector: Optional[str] = None
    value: Optional[str] = None
    url: Optional[str] = None
    timeout: Optional[int] = None
    retries: Optional[int] = None
    wait_until: Optional[str] = None  # for goto: 'load' | 'domcontentloaded' | 'networkidle'
    path: Optional[str] = None        # for screenshot path
    full_page: Optional[bool] = None  # for screenshot
    seconds: Optional[float] = None   # for sleep

@dataclass
class BotConfig:
    start_url: Optional[str]
    steps: List[Step]
    profile: str
    headless: bool
    browser: str              # chromium | firefox | webkit
    default_timeout: int      # ms
    step_default_retries: int

    @staticmethod
    def from_dict(d: Dict[str, Any]) -> "BotConfig":
        steps = [Step(**s) for s in d.get("steps", [])]
        return BotConfig(
            start_url=d.get("start_url"),
            steps=steps,
            profile=d.get("profile", "./pw_profile"),
            headless=bool(d.get("headless", False)),
            browser=str(d.get("browser", "chromium")).lower(),
            default_timeout=int(d.get("default_timeout", 15000)),
            step_default_retries=int(d.get("step_default_retries", 2)),
        )

# ------------------------------ runner --------------------------------

class AutoBot:
    def __init__(self, cfg: BotConfig):
        self.cfg = cfg
        self.context = None
        self.page = None

    def _get_browser_type(self, p):
        b = self.cfg.browser
        if b == "chromium":
            return p.chromium
        if b == "firefox":
            return p.firefox
        if b == "webkit":
            return p.webkit
        raise ValueError(f"Unsupported browser type: {b}")

    def _launch(self, p):
        bt = self._get_browser_type(p)
        profile_dir = Path(self.cfg.profile).resolve()
        profile_dir.mkdir(parents=True, exist_ok=True)
        # Use persistent context to reuse cookies/localStorage
        self.context = bt.launch_persistent_context(
            user_data_dir=str(profile_dir),
            headless=self.cfg.headless,
            viewport={"width": 1366, "height": 820},
            args=["--disable-blink-features=AutomationControlled"],
        )
        self.context.set_default_timeout(self.cfg.default_timeout)
        self.page = self.context.pages[0] if self.context.pages else self.context.new_page()

    # --------------- actions ---------------
    def _do_goto(self, step: Step):
        wait_until = step.wait_until or "domcontentloaded"
        url = step.url
        if not url:
            raise ValueError("goto requires 'url'")
        self.page.goto(url, wait_until=wait_until)

    def _do_wait(self, step: Step):
        if not step.selector:
            raise ValueError("wait action requires 'selector'")
        self.page.wait_for_selector(step.selector, timeout=step.timeout or self.cfg.default_timeout)

    def _do_click(self, step: Step):
        if not step.selector:
            raise ValueError("click action requires 'selector'")
        self.page.click(step.selector, timeout=step.timeout or self.cfg.default_timeout)

    def _do_fill(self, step: Step):
        if not step.selector:
            raise ValueError("fill action requires 'selector'")
        self.page.fill(step.selector, step.value or "", timeout=step.timeout or self.cfg.default_timeout)

    def _do_press(self, step: Step):
        if not step.selector or not step.value:
            raise ValueError("press action requires 'selector' and 'value' (key)")
        self.page.press(step.selector, step.value, timeout=step.timeout or self.cfg.default_timeout)

    def _do_screenshot(self, step: Step):
        path = step.path or "screenshot.png"
        full = bool(step.full_page) if step.full_page is not None else True
        self.page.screenshot(path=path, full_page=full)
        log("info", f"screenshot saved", {"path": path, "full_page": full})

    def _do_sleep(self, step: Step):
        secs = float(step.seconds or 1.0)
        time.sleep(secs)

    def run(self) -> int:
        with sync_playwright() as p:
            self._launch(p)

            if self.cfg.start_url:
                log("info", "navigating to start_url", {"url": self.cfg.start_url})
                self.page.goto(self.cfg.start_url, wait_until="domcontentloaded")

            for i, st in enumerate(self.cfg.steps, start=1):
                action = (st.action or "").lower().strip()
                retries = st.retries if st.retries is not None else self.cfg.step_default_retries
                attempt = 0
                while True:
                    attempt += 1
                    try:
                        log("info", f"step {i}: {action}", {"attempt": attempt})
                        if action == "goto":
                            self._do_goto(st)
                        elif action == "wait":
                            self._do_wait(st)
                        elif action == "click":
                            self._do_click(st)
                        elif action == "fill":
                            self._do_fill(st)
                        elif action == "press":
                            self._do_press(st)
                        elif action == "screenshot":
                            self._do_screenshot(st)
                        elif action == "sleep":
                            self._do_sleep(st)
                        else:
                            raise ValueError(f"Unknown action: {action}")
                        break  # success
                    except PWTimeout as e:
                        log("warn", f"timeout on step {i}", {"error": str(e)[:200]})
                        if attempt > max(1, retries):
                            raise
                        time.sleep(0.2)
                    except Exception as e:
                        log("error", f"failed step {i}", {"error": str(e)[:300]})
                        if attempt > max(1, retries):
                            raise
                        time.sleep(0.2)

            # keep browser open briefly for inspection if not headless
            if not self.cfg.headless:
                log("info", "run finished; keeping browser open for 5s (not headless)")
                time.sleep(5)

            self.context.close()
            return 0

# ------------------------------ cli -----------------------------------

def parse_args() -> argparse.Namespace:
    ap = argparse.ArgumentParser(description="Playwright config-driven browser automation")
    ap.add_argument("--config", type=Path, required=True, help="Path to JSON/JSONC config")
    ap.add_argument("--profile", type=Path, help="Override user data dir")
    ap.add_argument("--headless", type=str, help="0/1 override")
    ap.add_argument("--browser", type=str, choices=["chromium", "firefox", "webkit"], help="Override browser type")
    ap.add_argument("--timeout", type=int, help="Default timeout (ms)")
    ap.add_argument("--retries", type=int, help="Default per-step retries")
    return ap.parse_args()

def main() -> int:
    args = parse_args()
    raw = load_json_or_jsonc(args.config)
    cfg = BotConfig.from_dict(raw)

    if args.profile: cfg.profile = str(args.profile)
    if args.headless is not None: cfg.headless = str2bool(args.headless)
    if args.browser: cfg.browser = args.browser.lower()
    if args.timeout: cfg.default_timeout = int(args.timeout)
    if args.retries is not None: cfg.step_default_retries = int(args.retries)

    log("info", "starting playwright autobot", {
        "profile": cfg.profile, "headless": cfg.headless,
        "browser": cfg.browser, "timeout_ms": cfg.default_timeout,
        "default_retries": cfg.step_default_retries
    })

    try:
        bot = AutoBot(cfg)
        return bot.run()
    except Exception as e:
        log("error", "automation failed", {"error": str(e)})
        return 1

if __name__ == "__main__":
    sys.exit(main())
