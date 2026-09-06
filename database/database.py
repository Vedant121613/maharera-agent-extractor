"""
Synchronous SQLite database layer.
All operations use the standard library sqlite3 — no async needed.
"""

import sqlite3
from datetime import datetime
from pathlib import Path
from typing import Optional

from database.models import Agent
from utils.logger import setup_logger

logger = setup_logger(__name__)

# ── Schema ────────────────────────────────────────────────────────────────────

_CREATE_AGENTS = """
CREATE TABLE IF NOT EXISTS agents (
    id                  INTEGER PRIMARY KEY AUTOINCREMENT,
    agent_id            TEXT    UNIQUE NOT NULL,
    agent_name          TEXT    DEFAULT '',
    first_name          TEXT    DEFAULT '',
    middle_name         TEXT    DEFAULT '',
    last_name           TEXT    DEFAULT '',
    father_name         TEXT    DEFAULT '',
    certificate_no      TEXT    DEFAULT '',
    registration_date   TEXT    DEFAULT '',
    validity_end_date   TEXT    DEFAULT '',
    status              TEXT    DEFAULT '',
    mobile              TEXT    DEFAULT '',
    alternate_mobile    TEXT    DEFAULT '',
    office_phone        TEXT    DEFAULT '',
    email               TEXT    DEFAULT '',
    website             TEXT    DEFAULT '',
    unit_number         TEXT    DEFAULT '',
    building_name       TEXT    DEFAULT '',
    street_name         TEXT    DEFAULT '',
    locality            TEXT    DEFAULT '',
    landmark            TEXT    DEFAULT '',
    city                TEXT    DEFAULT '',
    taluka              TEXT    DEFAULT '',
    district            TEXT    DEFAULT '',
    state               TEXT    DEFAULT 'Maharashtra',
    pincode             TEXT    DEFAULT '',
    address             TEXT    DEFAULT '',
    collection_status   TEXT    DEFAULT 'pending',
    failure_reason      TEXT,
    collected_at        TEXT,
    created_at          TEXT    DEFAULT CURRENT_TIMESTAMP
);
"""

_CREATE_IDX_STATUS = (
    "CREATE INDEX IF NOT EXISTS idx_status ON agents(collection_status);"
)

_COLUMNS = [
    "agent_id", "agent_name", "first_name", "middle_name", "last_name",
    "father_name", "certificate_no", "registration_date", "validity_end_date",
    "status", "mobile", "alternate_mobile", "office_phone", "email", "website",
    "unit_number", "building_name", "street_name", "locality", "landmark",
    "city", "taluka", "district", "state", "pincode", "address",
    "collection_status", "failure_reason", "collected_at", "created_at",
]


class Database:
    """
    Thin wrapper around sqlite3 for persisting agent records.

    Usage:
        db = Database("data/agents.db")
        # db is ready to use immediately — no .initialize() call needed.
    """

    def __init__(self, db_path: str | Path = "data/agents.db") -> None:
        self._path = Path(db_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._init_schema()
        logger.info(f"Database ready: {self._path}")

    # ── Schema init ───────────────────────────────────────────────────────────

    def _init_schema(self) -> None:
        with self._connect() as conn:
            conn.execute(_CREATE_AGENTS)
            conn.execute(_CREATE_IDX_STATUS)

    # ── Connection helper ─────────────────────────────────────────────────────

    def _connect(self) -> sqlite3.Connection:
        conn = sqlite3.connect(self._path, timeout=30.0)  # 30 second timeout for locks
        conn.row_factory = sqlite3.Row
        conn.execute("PRAGMA journal_mode=WAL;")
        conn.execute("PRAGMA busy_timeout=30000;")  # 30 seconds in milliseconds
        return conn

    # ── Writes ────────────────────────────────────────────────────────────────

    def upsert_agent(self, data: dict) -> bool:
        """
        Insert or update an agent row.
        `data` must contain at least 'agent_id'.
        Returns True on success.
        """
        if not data.get("agent_id"):
            logger.warning("upsert_agent called without agent_id — skipped.")
            return False

        try:
            # Only write columns that exist in the schema
            row = {k: data[k] for k in _COLUMNS if k in data}
            cols = list(row.keys())
            placeholders = ", ".join(["?"] * len(cols))
            updates = ", ".join(f"{c} = excluded.{c}" for c in cols if c != "agent_id")

            sql = (
                f"INSERT INTO agents ({', '.join(cols)}) VALUES ({placeholders}) "
                f"ON CONFLICT(agent_id) DO UPDATE SET {updates}"
            )
            with self._connect() as conn:
                conn.execute(sql, list(row.values()))
            return True

        except Exception as exc:
            logger.error(f"upsert_agent failed for {data.get('agent_id')}: {exc}")
            return False

    def mark_collected(self, agent_id: str) -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE agents SET collection_status='collected', "
                "collected_at=? WHERE agent_id=?",
                (datetime.utcnow().isoformat(timespec="seconds"), agent_id),
            )

    def mark_failed(self, agent_id: str, reason: str = "") -> None:
        with self._connect() as conn:
            conn.execute(
                "UPDATE agents SET collection_status='failed', failure_reason=? "
                "WHERE agent_id=?",
                (reason[:500], agent_id),
            )

    def reset_failed(self) -> int:
        """Reset all failed agents back to 'pending' for retry."""
        with self._connect() as conn:
            cur = conn.execute(
                "UPDATE agents SET collection_status='pending', failure_reason=NULL "
                "WHERE collection_status='failed'"
            )
            return cur.rowcount

    # ── Reads ─────────────────────────────────────────────────────────────────

    def agent_exists(self, agent_id: str) -> bool:
        with self._connect() as conn:
            row = conn.execute(
                "SELECT 1 FROM agents WHERE agent_id=?", (agent_id,)
            ).fetchone()
            return row is not None

    def get_pending_agents(self, limit: int = 100) -> list[str]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT agent_id FROM agents "
                "WHERE collection_status IN ('pending') "
                "ORDER BY id LIMIT ?",
                (limit,),
            ).fetchall()
            return [r["agent_id"] for r in rows]

    def get_all_agents(self) -> list[dict]:
        with self._connect() as conn:
            rows = conn.execute(
                "SELECT * FROM agents WHERE collection_status='collected' "
                "ORDER BY id"
            ).fetchall()
            return [dict(r) for r in rows]

    def get_stats(self) -> dict:
        with self._connect() as conn:
            total   = conn.execute("SELECT COUNT(*) FROM agents").fetchone()[0]
            collected = conn.execute(
                "SELECT COUNT(*) FROM agents WHERE collection_status='collected'"
            ).fetchone()[0]
            failed  = conn.execute(
                "SELECT COUNT(*) FROM agents WHERE collection_status='failed'"
            ).fetchone()[0]
            pending = conn.execute(
                "SELECT COUNT(*) FROM agents WHERE collection_status='pending'"
            ).fetchone()[0]
        return {
            "total": total,
            "collected": collected,
            "failed": failed,
            "pending": pending,
        }
