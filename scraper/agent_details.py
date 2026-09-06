"""
Extracts full agent detail from an individual agent page.
Tries JSON-in-script extraction first, then falls back to HTML table parsing.
"""

import json
import re
from typing import Optional

from bs4 import BeautifulSoup                 # ← was missing in the old file
from playwright.sync_api import Page

from utils.logger import setup_logger

logger = setup_logger(__name__)

# Fields we want to pull from embedded JS data
_JS_FIELDS = {
    "firstName":               "first_name",
    "middleName":              "middle_name",
    "lastName":                "last_name",
    "mobileNo":                "mobile",
    "emailId":                 "email",
    "reraRegistrationNumber":  "certificate_no",
    "reraRegistrationDate":    "registration_date",
    "reraRegistrationEndDate": "validity_end_date",
    "fatherFullName":          "father_name",
    "agentName":               "agent_name",
    "address":                 "address",
    "city":                    "city",
    "district":                "district",
    "state":                   "state",
    "pincode":                 "pincode",
}

# Labels on the visible HTML table / detail view
_TABLE_LABELS = {
    "First Name":                    "first_name",
    "Middle Name":                   "middle_name",
    "Last Name":                     "last_name",
    "Father Name":                   "father_name",
    "Mobile Number":                 "mobile",
    "Mobile No":                     "mobile",
    "Email ID":                      "email",
    "Email Id":                      "email",
    "Registration Date":             "registration_date",
    "Certificate Validity End Date": "validity_end_date",
    "Valid Upto":                    "validity_end_date",
    "Certificate Number":            "certificate_no",
    "Aadhar Number":                 "aadhar",
    "PAN Number":                    "pan",
    "GSTIN Number":                  "gstin",
    "Address":                       "address",
    "City":                          "city",
    "District":                      "district",
    "State":                         "state",
    "Pincode":                       "pincode",
}


class AgentDetailsScraper:
    """
    Extracts structured agent data from the detail page.

    Usage:
        scraper = AgentDetailsScraper(page)
        data = scraper.extract_details()   # returns dict or None
    """

    def __init__(self, page: Page) -> None:
        self._page = page

    # ── Public API ────────────────────────────────────────────────────────────

    def extract_details(self) -> Optional[dict]:
        """
        Try multiple extraction strategies in order of reliability.
        Returns a flat dict of agent fields, or None if nothing found.
        """
        try:
            self._page.wait_for_load_state("networkidle")
            html = self._page.content()
            
            # Save HTML for debugging
            logger.debug(f"Page title: {self._page.title()}")
            logger.debug(f"Page URL: {self._page.url}")

            # Strategy 1: JSON blob in <script> tags
            data = self._extract_from_scripts(html)
            if data:
                logger.info(f"Details extracted via JS: {list(data.keys())}")
                return data

            # Strategy 2: Visible HTML table / labelled elements
            data = self._extract_from_html(html)
            if data:
                logger.info(f"Details extracted via HTML: {list(data.keys())}")
                return data

            # Save failed page HTML for debugging
            logger.warning("No details found. Saving page HTML to debug_agent_page.html")
            with open("debug_agent_page.html", "w", encoding="utf-8") as f:
                f.write(html)
            
            logger.warning(f"No mobile or email found. Extracted fields: {list(data.keys()) if data else 'None'}")
            
            return None

        except Exception as exc:
            logger.error(f"extract_details failed: {exc}", exc_info=True)
            return None

    # ── Strategy 1: Script tag extraction ────────────────────────────────────

    def _extract_from_scripts(self, html: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")
        scripts = soup.find_all("script")

        for script in scripts:
            src = script.string or ""
            if not src.strip():
                continue

            # Try to find and parse a JSON object assigned to a JS variable
            for pattern in [
                r"(?:var\s+\w+\s*=\s*)(\{[^;]+\})\s*;",
                r"(?:agentData\s*=\s*)(\{[^;]+\})",
                r"(?:data\s*:\s*)(\{[^}]+\})",
            ]:
                for m in re.finditer(pattern, src, re.DOTALL):
                    try:
                        obj = json.loads(m.group(1))
                        result = self._map_js_fields(obj)
                        if result:
                            return result
                    except (json.JSONDecodeError, ValueError):
                        continue

            # Direct field-by-field regex scan
            result = {}
            for js_key, dest_key in _JS_FIELDS.items():
                m = re.search(
                    r'"' + re.escape(js_key) + r'"\s*:\s*"([^"]*)"', src
                )
                if m and m.group(1).strip():
                    result[dest_key] = m.group(1).strip()

            if result:
                return result

        return None

    def _map_js_fields(self, obj: dict) -> dict:
        """Map a parsed JS object's keys to our field names."""
        result = {}
        for js_key, dest_key in _JS_FIELDS.items():
            val = obj.get(js_key, "")
            if val and str(val).strip():
                result[dest_key] = str(val).strip()
        return result

    # ── Strategy 2: HTML table/label extraction ───────────────────────────────

    def _extract_from_html(self, html: str) -> Optional[dict]:
        soup = BeautifulSoup(html, "lxml")
        result = {}

        # ── Look for divs/elements with label-value pairs ─────────────────────
        # The MahaRERA page has structure like:
        #   <div class="label">First Name</div><div>ONKAR</div>
        for label_text, key in _TABLE_LABELS.items():
            # Find elements containing the label
            for elem in soup.find_all(string=re.compile(re.escape(label_text), re.IGNORECASE)):
                parent = elem.find_parent()
                if not parent:
                    continue
                
                # Try next sibling
                sibling = parent.find_next_sibling()
                if sibling:
                    val = sibling.get_text(strip=True)
                    if val and val not in ("", "-", "N/A", "NA") and not val.startswith("XXX"):
                        result[key] = val
                        continue
                
                # Try parent's next sibling
                if parent.parent:
                    next_elem = parent.parent.find_next_sibling()
                    if next_elem:
                        val = next_elem.get_text(strip=True)
                        if val and val not in ("", "-", "N/A", "NA") and not val.startswith("XXX"):
                            result[key] = val

        # ── Table rows (label | value) ────────────────────────────────────────
        for row in soup.find_all("tr"):
            cells = row.find_all("td")
            if len(cells) >= 2:
                label = cells[0].get_text(strip=True)
                value = cells[1].get_text(strip=True)
                for lbl, key in _TABLE_LABELS.items():
                    if lbl.lower() in label.lower() and value:
                        if value not in ("", "-", "N/A", "NA") and not value.startswith("XXX"):
                            result[key] = value
                            break

        return result if result else None
