"""
CAPTCHA detection and solving orchestration.
Solver priority: openai → local → twocaptcha (configurable via CAPTCHA_SOLVER_TYPE).
"""

import time
from typing import Optional

from playwright.sync_api import Page

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

_IMG_SELECTORS = [
    "canvas",                           # MahaRERA uses canvas for CAPTCHA!
    "img[src*='captcha']",
    "img[src*='Captcha']",
    "#captchaImg",
    "img[id*='captcha']",
    "img[class*='captcha']",
    ".captcha-image",
    "img[alt*='captcha']",
    "img[alt*='Captcha']",
]
_INPUT_SELECTORS = [
    "input[name='txtInput']",           # MahaRERA specific field name
    "input[id='txtInput']",
    "input[name*='captcha']",
    "input[id*='captcha']",
    "input[placeholder*='aptcha']",
    "#captchaInput",
]


class CaptchaHandler:
    """
    Detects a CAPTCHA on a Playwright page, solves it, and submits the answer.

    Supported solver types (set CAPTCHA_SOLVER_TYPE in .env):
        openai     — GPT-4o vision (best accuracy, requires OPENAI_API_KEY)
        local      — Tesseract OCR (free, needs Tesseract installed)
        twocaptcha — 2Captcha paid API (requires TWOCAPTCHA_API_KEY)
        auto       — tries openai → local → twocaptcha in order

    Usage:
        handler = CaptchaHandler()
        success = handler.handle_captcha(page)
    """

    MAX_ATTEMPTS = 7  # Increased attempts for better success rate

    def __init__(self) -> None:
        self._claude = None
        self._openai = None
        self._local = None
        self._third_party = None
        self._init_solvers()

    # ── Public API ────────────────────────────────────────────────────────────

    def handle_captcha(self, page: Page) -> bool:
        """
        Detect, solve, and submit the CAPTCHA on `page`.
        Returns True if no CAPTCHA is present or it was solved successfully.
        """
        logger.debug(">>> handle_captcha STARTED")
        
        # Set up automatic alert dismissal
        try:
            page.on("dialog", lambda dialog: dialog.accept())
            logger.debug("Dialog auto-dismissal enabled")
        except Exception:
            pass
        
        try:
            if not self._detect(page):
                logger.debug("No CAPTCHA found on page.")
                return True

            for attempt in range(1, self.MAX_ATTEMPTS + 1):
                logger.info(f"CAPTCHA detected — attempt {attempt}/{self.MAX_ATTEMPTS}")
                logger.debug(f"About to call _solve_and_submit, attempt {attempt}")
                result = self._solve_and_submit(page)
                logger.debug(f"_solve_and_submit returned: {result}")
                if result:
                    logger.debug(">>> handle_captcha SUCCEEDED")
                    return True
                time.sleep(1)  # Reduced wait time
                self._try_refresh(page)

            logger.warning("CAPTCHA could not be solved after all attempts.")
            logger.debug(">>> handle_captcha FAILED")
            return False
        except Exception as exc:
            logger.error(f"handle_captcha threw exception: {type(exc).__name__}: {exc}", exc_info=True)
            logger.debug(">>> handle_captcha EXCEPTION")
            raise

    # ── Solver initialisation ─────────────────────────────────────────────────

    def _init_solvers(self) -> None:
        """Initialize only LOCAL Tesseract solver"""
        mode = Config.CAPTCHA_SOLVER_TYPE

        if mode == "local":
            try:
                from captcha.local_solver import LocalCaptchaSolver
                self._local = LocalCaptchaSolver()
                logger.debug("Local (Tesseract) CAPTCHA solver ready.")
            except Exception as exc:
                logger.warning(f"Local solver not available: {exc}")
                self._local = None
        else:
            logger.warning(f"Unknown solver: {mode} — only 'local' is supported.")
            self._local = None

        if mode in ("twocaptcha", "auto"):
            try:
                from captcha.third_party import ThirdPartySolver
                self._third_party = ThirdPartySolver()
                logger.debug("2Captcha solver ready.")
            except Exception as exc:
                logger.warning(f"2Captcha solver not available: {exc}")

    # ── Core solve logic ──────────────────────────────────────────────────────

    def _solve(self, image_bytes: bytes) -> Optional[str]:
        mode = Config.CAPTCHA_SOLVER_TYPE
        logger.debug(f"_solve called with mode={mode}")

        if mode == "claude":
            logger.debug("Trying Claude solver")
            return self._claude.solve_captcha(image_bytes) if self._claude else None

        if mode == "openai":
            logger.debug("Trying OpenAI solver")
            if not self._openai:
                logger.error("OpenAI solver is None!")
                return None
            try:
                result = self._openai.solve_captcha(image_bytes)
                logger.debug(f"OpenAI solver returned: {result!r}")
                return result
            except Exception as exc:
                logger.error(f"OpenAI solver threw exception: {type(exc).__name__}: {exc}", exc_info=True)
                return None

        if mode == "local":
            logger.debug("Trying local solver")
            return self._local.solve_captcha(image_bytes) if self._local else None

        if mode == "twocaptcha":
            logger.debug("Trying 2captcha solver")
            return self._third_party.solve_captcha(image_bytes) if self._third_party else None

        # auto: claude → openai → local → twocaptcha
        logger.debug("Using auto mode, trying all solvers")
        for solver in (self._claude, self._openai, self._local, self._third_party):
            if solver:
                result = solver.solve_captcha(image_bytes)
                if result:
                    return result

        return None

    def _solve_and_submit(self, page: Page) -> bool:
        logger.debug(">>> _solve_and_submit STARTED")
        
        image_bytes = self._get_image_bytes(page)
        if not image_bytes:
            logger.warning("Could not capture CAPTCHA image.")
            return False

        logger.debug(f"Calling _solve with {len(image_bytes)} bytes")
        solution = self._solve(image_bytes)
        logger.debug(f"_solve returned: {solution!r}")
        
        if not solution:
            logger.warning("All solvers returned no result.")
            return False

        logger.info(f"CAPTCHA solution received: {solution!r}")
        
        captcha_input = self._get_input(page)
        if not captcha_input:
            logger.warning("CAPTCHA input field not found.")
            return False

        logger.debug("About to type CAPTCHA solution")
        # Clear and type solution slowly
        captcha_input.click()
        captcha_input.fill("")
        time.sleep(0.5)
        captcha_input.type(solution, delay=100)
        logger.info(f"Typed CAPTCHA solution: {solution!r}")
        time.sleep(1)

        logger.debug("About to submit CAPTCHA")
        # Submit - look for the "Submit" button specifically
        submit_selectors = [
            "button:has-text('Submit')",
            "input[type='submit']",
            "button[type='submit']",
            "input[value='Submit']",
        ]
        
        clicked = False
        for sel in submit_selectors:
            submit = page.locator(sel)
            if submit.count() > 0:
                submit.first.click()
                logger.info(f"Clicked submit button: {sel}")
                clicked = True
                break
        
        if not clicked:
            captcha_input.press("Enter")
            logger.info("Pressed Enter on CAPTCHA input")

        time.sleep(1)
        
        # Handle any alert dialogs (invalid CAPTCHA popup)
        try:
            # Check if there's an alert/dialog
            page.wait_for_timeout(500)
            
            # Try to dismiss any alerts by pressing Enter or clicking OK
            try:
                # Handle browser dialogs
                page.on("dialog", lambda dialog: dialog.accept())
                logger.debug("Set up dialog handler")
            except:
                pass
            
            # Also try to click any visible "OK" button in modal
            ok_buttons = [
                "button:has-text('OK')",
                "button:has-text('Ok')",
                "button.btn:has-text('OK')",
                ".modal button:has-text('OK')",
            ]
            for ok_sel in ok_buttons:
                ok_btn = page.locator(ok_sel)
                if ok_btn.count() > 0 and ok_btn.first.is_visible():
                    ok_btn.first.click()
                    logger.debug(f"Clicked OK button: {ok_sel}")
                    time.sleep(0.5)
                    break
        except Exception as alert_exc:
            logger.debug(f"No alert to handle: {alert_exc}")

        time.sleep(1)  # Wait for page to process
        
        logger.debug("Checking if CAPTCHA was accepted")
        # Check if still on CAPTCHA page (failed) or moved to details (success)
        try:
            page.wait_for_load_state("networkidle", timeout=8000)
            # If CAPTCHA still visible, it failed
            if self._detect(page):
                logger.warning("CAPTCHA still present after submit - solution was wrong")
                return False
            logger.info("CAPTCHA solved successfully - details page loaded")
            logger.debug(">>> _solve_and_submit SUCCEEDED")
            return True
        except Exception as exc:
            logger.warning(f"Timeout waiting for page load: {exc}")
            return False

    # ── Page helpers ──────────────────────────────────────────────────────────

    def _detect(self, page: Page) -> bool:
        for sel in _IMG_SELECTORS + _INPUT_SELECTORS:
            if page.locator(sel).count() > 0:
                return True
        return False

    def _get_image_bytes(self, page: Page) -> Optional[bytes]:
        """Try multiple strategies to capture CAPTCHA image."""
        
        # Strategy 1: Try known selectors
        for sel in _IMG_SELECTORS:
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    screenshot = loc.first.screenshot()
                    logger.info(f"Captured CAPTCHA via selector: {sel}")
                    # Save for debugging
                    with open("captcha_debug.png", "wb") as f:
                        f.write(screenshot)
                    logger.info("CAPTCHA image saved to captcha_debug.png")
                    return screenshot
                except Exception as exc:
                    logger.debug(f"Screenshot failed for {sel}: {exc}")
        
        # Strategy 2: Try modal screenshot
        try:
            modal = page.locator(".modal-content, .modal-body, [role='dialog']").first
            if modal.count() > 0:
                screenshot = modal.screenshot()
                logger.info("Captured CAPTCHA via modal screenshot")
                with open("captcha_debug.png", "wb") as f:
                    f.write(screenshot)
                return screenshot
        except Exception:
            pass
        
        return None

    def _get_input(self, page: Page):
        for sel in _INPUT_SELECTORS:
            loc = page.locator(sel)
            if loc.count() > 0:
                return loc.first
        return None

    @staticmethod
    def _try_refresh(page: Page) -> None:
        for sel in ["a[href*='captcha']", "#refreshCaptcha", ".captcha-refresh"]:
            loc = page.locator(sel)
            if loc.count() > 0:
                try:
                    loc.first.click()
                    time.sleep(1)
                except Exception:
                    pass
                return
