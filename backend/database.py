"""SQLite persistence for SentinelAI alerts and telemetry."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sentinel.db"


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS assets (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                asset_type TEXT NOT NULL,
                status TEXT DEFAULT 'NORMAL'
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                event TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                temp_c REAL,
                light_level INTEGER,
                door_open INTEGER,
                flame_detected INTEGER,
                payload TEXT,
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                incident_status TEXT DEFAULT 'Open'
            );

            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                temp_c REAL,
                light_level INTEGER,
                door_open INTEGER,
                flame_detected INTEGER,
                maintenance_mode INTEGER,
                created_at TEXT NOT NULL
            );
            """
        )
        # Seed demo asset if empty
        row = conn.execute("SELECT COUNT(*) FROM assets").fetchone()
        if row and row[0] == 0:
            conn.execute(
                """
                INSERT INTO assets (id, name, lat, lon, asset_type, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "TRANSFORMER-001",
                    "Industrial District Transformer",
                    -26.1788,
                    28.0195,
                    "electrical_transformer",
                    "NORMAL",
                ),
            )
            conn.execute(
                """
                INSERT INTO assets (id, name, lat, lon, asset_type, status)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    "CABLE-VAULT-002",
                    "Cable Compartment — Substation East",
                    -26.1800,
                    28.0220,
                    "cable_vault",
                    "NORMAL",
                ),
            )


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def insert_alert(record: Dict[str, Any]) -> int:
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts (
                asset_id, event, severity, message, risk_score, risk_level, status,
                temp_c, light_level, door_open, flame_detected, payload, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["asset_id"],
                record["event"],
                record["severity"],
                record.get("message", ""),
                record["risk_score"],
                record["risk_level"],
                record["status"],
                record.get("temp_c"),
                record.get("light_level"),
                1 if record.get("door_open") else 0,
                1 if record.get("flame_detected") else 0,
                json.dumps(record.get("payload", {})),
                record.get("created_at", datetime.now().isoformat()),
            ),
        )
        conn.execute(
            "UPDATE assets SET status = ? WHERE id = ?",
            (record["status"], record["asset_id"]),
        )
        return int(cur.lastrowid)


def insert_telemetry(record: Dict[str, Any]) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO telemetry (
                asset_id, temp_c, light_level, door_open, flame_detected,
                maintenance_mode, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["asset_id"],
                record.get("temp_c"),
                record.get("light_level"),
                1 if record.get("door_open") else 0,
                1 if record.get("flame_detected") else 0,
                1 if record.get("maintenance_mode") else 0,
                record.get("created_at", datetime.now().isoformat()),
            ),
        )


def list_alerts(limit: int = 50) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            """
            SELECT * FROM alerts ORDER BY id DESC LIMIT ?
            """,
            (limit,),
        ).fetchall()
    return [dict(r) for r in rows]


def list_assets() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM assets ORDER BY id").fetchall()
    return [dict(r) for r in rows]


def get_latest_telemetry(asset_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            """
            SELECT * FROM telemetry WHERE asset_id = ?
            ORDER BY id DESC LIMIT 1
            """,
            (asset_id,),
        ).fetchone()
    return dict(row) if row else None


def update_incident(alert_id: int, incident_status: str) -> bool:
    with get_connection() as conn:
        cur = conn.execute(
            "UPDATE alerts SET incident_status = ? WHERE id = ?",
            (incident_status, alert_id),
        )
        return cur.rowcount > 0
