"""
Logging setup using loguru with console + rotating file output.
Call setup_logger() once per module; all calls share one configured instance.
"""

import sys
from pathlib import Path

from loguru import logger as _loguru_logger

_configured = False


def setup_logger(name: str = "maharera"):
    """Return a loguru logger bound to `name`. Configures handlers on first call."""
    global _configured
    if not _configured:
        from config.config import Config

        _loguru_logger.remove()  # Drop the default stderr handler

        # ── Console ───────────────────────────────────────────────────────────
        _loguru_logger.add(
            sys.stderr,
            level=Config.LOG_LEVEL,
            colorize=True,
            format=(
                "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                "<level>{level:<8}</level> | "
                "<cyan>{extra[name]}</cyan> - "
                "<level>{message}</level>"
            ),
        )

        # ── Rotating file ─────────────────────────────────────────────────────
        log_path = Path(Config.LOG_FILE)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        _loguru_logger.add(
            log_path,
            level="DEBUG",
            rotation="10 MB",
            retention="14 days",
            compression="zip",
            encoding="utf-8",
            format="{time:YYYY-MM-DD HH:mm:ss} | {level:<8} | {extra[name]} - {message}",
        )

        _configured = True

    return _loguru_logger.bind(name=name)
