"""
Export collected agent data to a UTF-8 CSV file.
"""

import csv
from pathlib import Path

from database.database import Database
from utils.logger import setup_logger

logger = setup_logger(__name__)

_FIELDNAMES = [
    "agent_id", "agent_name", "first_name", "middle_name", "last_name",
    "father_name", "certificate_no", "registration_date", "validity_end_date",
    "status", "mobile", "email", "address", "city", "district", "state",
    "pincode", "collected_at",
]


class CSVExporter:
    def __init__(self, db: Database) -> None:
        self._db = db

    def export(self, output_path: str | Path | None = None) -> Path:
        """
        Write all collected agents to a CSV file.

        Args:
            output_path: Full file path including .csv extension.
                         Defaults to <OUTPUT_DIR>/maharera_agents.csv
        """
        from config.config import Config
        from utils.helpers import timestamp_filename

        if output_path is None:
            fname = timestamp_filename("maharera_agents", ".csv")
            output_path = Path(Config.OUTPUT_DIR) / fname

        path = Path(output_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        agents = self._db.get_all_agents()

        # utf-8-sig adds the BOM so Excel opens without encoding issues
        with path.open("w", newline="", encoding="utf-8-sig") as fh:
            writer = csv.DictWriter(
                fh, fieldnames=_FIELDNAMES, extrasaction="ignore"
            )
            writer.writeheader()
            writer.writerows(agents)

        logger.info(f"CSV saved → {path}  ({len(agents)} rows)")
        return path
