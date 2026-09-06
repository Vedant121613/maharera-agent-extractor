"""
Sync Playwright browser manager with anti-detection hardening.
"""

import random
import time

from playwright.sync_api import sync_playwright, Browser, BrowserContext, Page, Playwright

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

_USER_AGENTS = [
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/123.0.0.0 Safari/537.36 Edg/123.0.0.0",
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 "
    "(KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
]


class BrowserManager:
    """
    Manages a single sync Playwright Chromium browser instance.

    Usage (context manager — recommended):
        with BrowserManager() as bm:
            page = bm.new_page()
            ...

    Usage (manual):
        bm = BrowserManager()
        bm.start()
        page = bm.new_page()
        ...
        bm.stop()
    """

    def __init__(self, headless: bool | None = None) -> None:
        self._headless = headless if headless is not None else Config.HEADLESS
        self._playwright: Playwright | None = None
        self._browser: Browser | None = None

    # ── Context manager ───────────────────────────────────────────────────────

    def __enter__(self) -> "BrowserManager":
        self.start()
        return self

    def __exit__(self, *_) -> None:
        self.stop()

    # ── Lifecycle ─────────────────────────────────────────────────────────────

    def start(self) -> None:
        logger.info("Starting browser...")
        self._playwright = sync_playwright().start()
        self._browser = self._playwright.chromium.launch(
            headless=self._headless,
            args=[
                "--disable-blink-features=AutomationControlled",
                "--no-sandbox",
                "--disable-setuid-sandbox",
                "--disable-dev-shm-usage",
                "--disable-infobars",
            ],
        )
        logger.info(f"Browser launched (headless={self._headless})")

    def stop(self) -> None:
        if self._browser:
            self._browser.close()
        if self._playwright:
            self._playwright.stop()
        logger.info("Browser closed")

    # ── Page / Context helpers ────────────────────────────────────────────────

    def new_context(self) -> BrowserContext:
        """Create a new browser context with randomised fingerprint."""
        if not self._browser:
            raise RuntimeError("Browser not started. Call start() first.")

        user_agent = random.choice(_USER_AGENTS)
        context = self._browser.new_context(
            user_agent=user_agent,
            viewport={
                "width": 1366 + random.randint(-80, 80),
                "height": 768 + random.randint(-40, 40),
            },
            locale="en-IN",
            timezone_id="Asia/Kolkata",
            java_script_enabled=True,
        )
        # Remove webdriver flag
        context.add_init_script(
            "Object.defineProperty(navigator, 'webdriver', {get: () => undefined})"
        )
        return context

    def new_page(self) -> Page:
        """Return a new page inside a fresh context."""
        context = self.new_context()
        page = context.new_page()
        page.set_default_timeout(Config.PAGE_LOAD_TIMEOUT)
        return page

    # ── Navigation ────────────────────────────────────────────────────────────

    def navigate(self, page: Page, url: str, wait: str = "networkidle") -> None:
        """Navigate to a URL and wait for the page to settle."""
        logger.debug(f"Navigating → {url[:100]}")
        page.goto(url, wait_until=wait, timeout=Config.PAGE_LOAD_TIMEOUT)
        self.random_delay()

    # ── Utilities ─────────────────────────────────────────────────────────────

    @staticmethod
    def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
        """Block for a random duration to mimic human behaviour."""
        time.sleep(random.uniform(min_s, max_s))

    @staticmethod
    def human_type(page: Page, selector: str, text: str) -> None:
        """Type text character-by-character with small random delays."""
        page.click(selector)
        for char in text:
            page.keyboard.type(char)
            time.sleep(random.uniform(0.05, 0.15))
