"""
Centralised configuration — loaded from .env via python-dotenv.
Every other module imports from here; nothing reads os.getenv directly.
"""

import os
import random
from pathlib import Path

from dotenv import load_dotenv

# Load .env from project root (works regardless of where Python is invoked)
load_dotenv(Path(__file__).resolve().parents[1] / ".env")


class Config:
    # ── URLs ──────────────────────────────────────────────────────────────────
    BASE_URL: str = os.getenv(
        "MAHARERA_BASE_URL", "https://maharera.maharashtra.gov.in"
    )
    AGENT_SEARCH_URL: str = os.getenv(
        "AGENT_SEARCH_URL",
        "https://maharera.maharashtra.gov.in/agents-search-result",
    )
    AGENT_DETAIL_BASE: str = os.getenv(
        "AGENT_DETAIL_BASE",
        "https://maharerait.maharashtra.gov.in/agent/view",
    )

    # ── Browser ───────────────────────────────────────────────────────────────
    HEADLESS: bool = os.getenv("HEADLESS", "true").lower() == "true"
    PAGE_LOAD_TIMEOUT: int = int(os.getenv("PAGE_LOAD_TIMEOUT", "30000"))

    # ── Rate limiting ─────────────────────────────────────────────────────────
    REQUEST_DELAY_MIN: float = float(os.getenv("REQUEST_DELAY_MIN", "2.0"))
    REQUEST_DELAY_MAX: float = float(os.getenv("REQUEST_DELAY_MAX", "5.0"))
    MAX_RETRIES: int = 3

    # ── CAPTCHA (FREE Tesseract - 7 attempts) ───────────────────────────────────
    CAPTCHA_SOLVER_TYPE: str = os.getenv("CAPTCHA_SOLVER_TYPE", "local")
    TESSERACT_CMD: str = os.getenv(
        "TESSERACT_CMD", r"/usr/bin/tesseract"  # Default for Linux/AWS
    )

    # ── Database ──────────────────────────────────────────────────────────────
    DB_PATH: str = os.getenv("DB_PATH", "data/agents.db")

    # ── Export ────────────────────────────────────────────────────────────────
    OUTPUT_DIR: str = os.getenv("OUTPUT_DIR", "output")

    # ── Logging ───────────────────────────────────────────────────────────────
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    LOG_FILE: str = os.getenv("LOG_FILE", "logs/extractor.log")

    # ── Helpers ───────────────────────────────────────────────────────────────
    @classmethod
    def get_random_delay(cls) -> float:
        """Return a random delay (seconds) within the configured range."""
        return random.uniform(cls.REQUEST_DELAY_MIN, cls.REQUEST_DELAY_MAX)

    @classmethod
    def get_detail_url(cls, agent_id) -> str:
        return f"{cls.AGENT_DETAIL_BASE}/{agent_id}"
