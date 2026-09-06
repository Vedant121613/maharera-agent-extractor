#!/usr/bin/env python3
"""
Retry failed agents — resets their status to 'pending' so the next
scrape run will attempt them again.

Usage:
    python scripts/retry_failed.py
    python scripts/retry_failed.py --run   # reset AND immediately re-scrape
"""

import argparse
import sys
from pathlib import Path

# Make sure project root is on the path when run as a script
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from config.config import Config
from database.database import Database
from utils.logger import setup_logger

logger = setup_logger("retry_failed")


def parse_args() -> argparse.Namespace:
    p = argparse.ArgumentParser(description="Retry failed MahaRERA agents")
    p.add_argument("--run", action="store_true",
                   help="After resetting, immediately re-scrape the pending agents")
    p.add_argument("--no-headless", dest="headless", action="store_false",
                   default=True, help="Show browser when re-scraping")
    return p.parse_args()


def main() -> None:
    args = parse_args()
    db = Database(Config.DB_PATH)

    stats_before = db.get_stats()
    print(f"Failed agents before reset: {stats_before['failed']}")

    count = db.reset_failed()
    print(f"Reset {count} agent(s) to 'pending'.")

    if args.run and count > 0:
        print("Re-scraping pending agents...\n")
        # Import here to avoid loading playwright unless --run is passed
        from main import phase2_collect_details
        phase2_collect_details(db, headless=args.headless, limit=None)

    stats_after = db.get_stats()
    print(f"\nStats after: {stats_after}")


if __name__ == "__main__":
    main()
