#!/usr/bin/env python3
"""
Cleanup script — removes old export files and compressed log archives.

Usage:
    python scripts/cleanup.py
    python scripts/cleanup.py --days 7
    python scripts/cleanup.py --dry-run
"""

import argparse
import time
from pathlib import Path


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Clean old output and log files")
    p.add_argument("--days",    type=int, default=30,
                   help="Delete files older than N days (default: 30)")
    p.add_argument("--dry-run", action="store_true",
                   help="List files that would be deleted without deleting")
    return p.parse_args()


def cleanup(days: int, dry_run: bool) -> None:
    cutoff = time.time() - days * 86_400
    root   = Path(__file__).resolve().parents[1]

    targets = [
        *root.glob("output/*.xlsx"),
        *root.glob("output/*.csv"),
        *root.glob("logs/*.zip"),
    ]

    deleted = 0
    for f in targets:
        if f.stat().st_mtime < cutoff:
            if dry_run:
                print(f"[DRY RUN] would delete: {f}")
            else:
                f.unlink()
                print(f"Deleted: {f}")
            deleted += 1

    action = "Would delete" if dry_run else "Deleted"
    print(f"\n{action} {deleted} file(s) older than {days} days.")


if __name__ == "__main__":
    args = parse_args()
    cleanup(args.days, args.dry_run)
