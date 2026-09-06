"""
Scrapes MahaRERA agent search result pages.
Extracts agent IDs and basic info from the paginated table.
"""

import re
import time
from typing import Optional

from bs4 import BeautifulSoup
from playwright.sync_api import Page

from config.config import Config
from utils.logger import setup_logger

logger = setup_logger(__name__)

# Regex to pull the numeric agent ID from a detail-page URL
_AGENT_ID_RE = re.compile(r"/agent/view/(\d+)", re.IGNORECASE)


class SearchPageScraper:
    """
    Parses a loaded search-results page and extracts agent rows.
    Pass a Playwright Page that has already navigated to the search URL.
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_agents(self) -> list[dict]:
        """
        Parse the current page HTML and return a list of dicts:
            { agent_id, agent_name, certificate_no }
        """
        agents: list[dict] = []
        try:
            html = self._page.content()
            soup = BeautifulSoup(html, "lxml")

            table = soup.find("table")
            if not table:
                logger.warning("No <table> found on search page.")
                return agents

            rows = table.find_all("tr")
            for row in rows[1:]:          # skip header
                cols = row.find_all("td")
                if len(cols) < 4:
                    continue

                agent_name = cols[1].get_text(strip=True)
                certificate_no = cols[2].get_text(strip=True)

                # Agent ID lives in the "View Details" link href
                link = cols[3].find("a") or row.find("a", href=_AGENT_ID_RE)
                agent_id: Optional[str] = None
                if link and link.get("href"):
                    m = _AGENT_ID_RE.search(link["href"])
                    if m:
                        agent_id = m.group(1)

                if agent_name and certificate_no and agent_id:
                    agents.append(
                        {
                            "agent_id": agent_id,
                            "agent_name": agent_name,
                            "certificate_no": certificate_no,
                        }
                    )

            logger.info(f"Found {len(agents)} agent(s) on page.")
        except Exception as exc:
            logger.error(f"extract_agents failed: {exc}", exc_info=True)

        return agents

    def get_total_pages(self) -> int:
        """
        Detect total page count from the pagination area.
        Falls back to a safe default so scraping always starts.
        """
        try:
            html = self._page.content()
            soup = BeautifulSoup(html, "lxml")
            text = soup.get_text(" ", strip=True)

            # Pattern: "Showing Final 58464 Result"
            m = re.search(r"Showing\s+Final\s+([\d,]+)\s+Result", text, re.IGNORECASE)
            if m:
                total = int(m.group(1).replace(",", ""))
                pages = (total // 10) + (1 if total % 10 else 0)
                logger.info(f"Total agents: {total} → {pages} pages")
                return pages

            # Pattern: "Pages X of Y"
            m = re.search(r"Pages?\s+\d+\s+of\s+(\d+)", text, re.IGNORECASE)
            if m:
                pages = int(m.group(1))
                logger.info(f"Total pages detected: {pages}")
                return pages

            # Check next button; if absent we're on the last page
            if not self._has_next():
                return 1

        except Exception as exc:
            logger.warning(f"get_total_pages failed: {exc}")

        logger.warning("Could not determine total pages — defaulting to 5847.")
        return 5847

    def navigate_to_page(self, page_num: int) -> bool:
        """
        Navigate to a numbered page.
        Returns True on success.
        """
        try:
            url = f"{Config.AGENT_SEARCH_URL}?page={page_num}"
            self._page.goto(url, wait_until="networkidle",
                            timeout=Config.PAGE_LOAD_TIMEOUT)
            time.sleep(Config.get_random_delay())
            return True
        except Exception as exc:
            logger.error(f"Failed to navigate to page {page_num}: {exc}")
            return False

    def click_next(self) -> bool:
        """Click the 'Next' pagination button. Returns True if clicked."""
        selectors = [
            "a:has-text('Next')",
            "a:has-text('next')",
            "li.next > a",
            "a.next",
            "[aria-label='Next page']",
        ]
        for sel in selectors:
            loc = self._page.locator(sel)
            if loc.count() > 0:
                try:
                    loc.first.click()
                    self._page.wait_for_load_state(
                        "networkidle", timeout=Config.PAGE_LOAD_TIMEOUT
                    )
                    time.sleep(Config.get_random_delay())
                    return True
                except Exception as exc:
                    logger.debug(f"click_next selector {sel!r} failed: {exc}")
        return False

    def _has_next(self) -> bool:
        selectors = ["a:has-text('Next')", "li.next > a", "a.next"]
        return any(self._page.locator(s).count() > 0 for s in selectors)
