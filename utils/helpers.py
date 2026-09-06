"""
General-purpose synchronous helper utilities.
"""

import random
import time
from datetime import datetime
from pathlib import Path
from typing import Any


def random_delay(min_s: float = 1.0, max_s: float = 3.0) -> None:
    """Block for a random duration between min_s and max_s seconds."""
    time.sleep(random.uniform(min_s, max_s))


def ensure_dir(path: str | Path) -> Path:
    """Create directory (and parents) if it doesn't exist. Returns the Path."""
    p = Path(path)
    p.mkdir(parents=True, exist_ok=True)
    return p


def timestamp_filename(base: str, ext: str) -> str:
    """
    Generate a timestamped filename.

    Example:
        timestamp_filename("export", ".xlsx") -> "export_20260830_143022.xlsx"
    """
    ts = datetime.now().strftime("%Y%m%d_%H%M%S")
    return f"{base}_{ts}{ext}"


def flatten_dict(d: dict, parent_key: str = "", sep: str = "_") -> dict:
    """Recursively flatten a nested dict."""
    items: list[tuple[str, Any]] = []
    for k, v in d.items():
        new_key = f"{parent_key}{sep}{k}" if parent_key else k
        if isinstance(v, dict):
            items.extend(flatten_dict(v, new_key, sep).items())
        else:
            items.append((new_key, v))
    return dict(items)


def chunk_list(lst: list, size: int) -> list[list]:
    """Split `lst` into sublists of at most `size` items."""
    return [lst[i: i + size] for i in range(0, len(lst), size)]
