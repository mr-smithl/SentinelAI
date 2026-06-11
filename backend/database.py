"""SQLite persistence for SentinelAI alerts, telemetry, and infrastructure sites."""

from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Generator, List, Optional

from backend.stations import STATUS_NORMAL, flatten_stations

DB_PATH = Path(__file__).resolve().parent.parent / "data" / "sentinel.db"

MONITORED_NODE = "TRANSFORMER-001"
MONITORED_SITE = "johannesburg-city-power-john-ware-substation"  # Updated to match prefixed ID format


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with get_connection() as conn:
        conn.executescript(
            """
            CREATE TABLE IF NOT EXISTS sites (
                id TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                category TEXT NOT NULL,
                facility_type TEXT,
                owner TEXT,
                lat REAL NOT NULL,
                lon REAL NOT NULL,
                status TEXT DEFAULT 'NORMAL',
                risk_score INTEGER DEFAULT 0,
                has_sensors INTEGER DEFAULT 0,
                sensor_node_id TEXT
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                site_id TEXT,
                event TEXT NOT NULL,
                severity TEXT NOT NULL,
                message TEXT,
                risk_score INTEGER NOT NULL,
                risk_level TEXT NOT NULL,
                status TEXT NOT NULL,
                intrusion_probability REAL,
                temp_c REAL,
                light_level INTEGER,
                door_open INTEGER,
                flame_detected INTEGER,
                motion_detected INTEGER,
                payload TEXT,
                audience TEXT DEFAULT 'all',
                created_at TEXT NOT NULL,
                resolved_at TEXT,
                incident_status TEXT DEFAULT 'Open'
            );

            CREATE TABLE IF NOT EXISTS telemetry (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                asset_id TEXT NOT NULL,
                site_id TEXT,
                temp_c REAL,
                light_level INTEGER,
                door_open INTEGER,
                flame_detected INTEGER,
                motion_detected INTEGER,
                maintenance_mode INTEGER,
                intrusion_probability REAL,
                created_at TEXT NOT NULL
            );

            CREATE TABLE IF NOT EXISTS notifications (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                audience TEXT NOT NULL,
                title TEXT NOT NULL,
                body TEXT NOT NULL,
                alert_id INTEGER,
                created_at TEXT NOT NULL
            );
            """
        )
        _migrate(conn)
        _seed_sites(conn)


def _migrate(conn: sqlite3.Connection) -> None:
    """Add columns when upgrading from earlier schema."""
    alert_cols = {r[1] for r in conn.execute("PRAGMA table_info(alerts)").fetchall()}
    for col, typedef in [
        ("site_id", "TEXT"),
        ("intrusion_probability", "REAL"),
        ("motion_detected", "INTEGER DEFAULT 0"),
        ("audience", "TEXT DEFAULT 'all'"),
    ]:
        if col not in alert_cols:
            conn.execute(f"ALTER TABLE alerts ADD COLUMN {col} {typedef}")

    tel_cols = {r[1] for r in conn.execute("PRAGMA table_info(telemetry)").fetchall()}
    for col, typedef in [
        ("site_id", "TEXT"),
        ("motion_detected", "INTEGER DEFAULT 0"),
        ("intrusion_probability", "REAL"),
    ]:
        if col not in tel_cols:
            conn.execute(f"ALTER TABLE telemetry ADD COLUMN {col} {typedef}")


def _seed_sites(conn: sqlite3.Connection) -> None:
    stations = flatten_stations()
    current_ids = set()
    for site in stations:
        current_ids.add(site["id"])
        conn.execute(
            """
            INSERT OR REPLACE INTO sites (
                id, name, category, facility_type, owner, lat, lon,
                status, risk_score, has_sensors, sensor_node_id
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                site["id"],
                site["name"],
                site["category"],
                site.get("facility_type"),
                site.get("owner"),
                site["lat"],
                site["lon"],
                site.get("status", STATUS_NORMAL),
                site.get("risk_score", 0),
                1 if site.get("has_sensors") else 0,
                site.get("sensor_node_id"),
            ),
        )

    if current_ids:
        existing_ids = {
            row["id"] for row in conn.execute("SELECT id FROM sites").fetchall()
        }
        stale_ids = existing_ids - current_ids
        for stale_id in stale_ids:
            conn.execute("DELETE FROM sites WHERE id = ?", (stale_id,))


@contextmanager
def get_connection() -> Generator[sqlite3.Connection, None, None]:
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def resolve_site_id(asset_id: str) -> str:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT id FROM sites WHERE sensor_node_id = ? LIMIT 1", (asset_id,)
        ).fetchone()
        if row:
            return row["id"]
        # Fallback: if asset_id not found, try the configured monitored node id
        row2 = conn.execute(
            "SELECT id FROM sites WHERE sensor_node_id = ? LIMIT 1", (MONITORED_NODE,)
        ).fetchone()
    return row2["id"] if row2 else MONITORED_SITE


def update_site_status(site_id: str, status: str, risk_score: int) -> None:
    with get_connection() as conn:
        conn.execute(
            "UPDATE sites SET status = ?, risk_score = ? WHERE id = ?",
            (status, risk_score, site_id),
        )


def insert_alert(record: Dict[str, Any]) -> int:
    site_id = record.get("site_id") or resolve_site_id(record["asset_id"])
    audience = record.get("audience", "all")
    with get_connection() as conn:
        cur = conn.execute(
            """
            INSERT INTO alerts (
                asset_id, site_id, event, severity, message, risk_score, risk_level,
                status, intrusion_probability, temp_c, light_level, door_open,
                flame_detected, motion_detected, payload, audience, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["asset_id"],
                site_id,
                record["event"],
                record["severity"],
                record.get("message", ""),
                record["risk_score"],
                record["risk_level"],
                record["status"],
                record.get("intrusion_probability"),
                record.get("temp_c"),
                record.get("light_level"),
                1 if record.get("door_open") else 0,
                1 if record.get("flame_detected") else 0,
                1 if record.get("motion_detected") else 0,
                json.dumps(record.get("payload", {})),
                audience,
                record.get("created_at", datetime.now().isoformat()),
            ),
        )
        conn.execute(
            "UPDATE sites SET status = ?, risk_score = ? WHERE id = ?",
            (record["status"], record["risk_score"], site_id),
        )
        return int(cur.lastrowid)


def insert_telemetry(record: Dict[str, Any]) -> None:
    site_id = record.get("site_id") or resolve_site_id(record["asset_id"])
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO telemetry (
                asset_id, site_id, temp_c, light_level, door_open, flame_detected,
                motion_detected, maintenance_mode, intrusion_probability, created_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                record["asset_id"],
                site_id,
                record.get("temp_c"),
                record.get("light_level"),
                1 if record.get("door_open") else 0,
                1 if record.get("flame_detected") else 0,
                1 if record.get("motion_detected") else 0,
                1 if record.get("maintenance_mode") else 0,
                record.get("intrusion_probability"),
                record.get("created_at", datetime.now().isoformat()),
            ),
        )
        if record.get("status"):
            conn.execute(
                "UPDATE sites SET status = ?, risk_score = ? WHERE id = ?",
                (record["status"], record.get("risk_score", 0), site_id),
            )


def insert_notification(audience: str, title: str, body: str, alert_id: Optional[int] = None) -> None:
    with get_connection() as conn:
        conn.execute(
            """
            INSERT INTO notifications (audience, title, body, alert_id, created_at)
            VALUES (?, ?, ?, ?, ?)
            """,
            (audience, title, body, alert_id, datetime.now().isoformat()),
        )


def list_alerts(limit: int = 50, audience: Optional[str] = None) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        if audience == "security":
            rows = conn.execute(
                """
                SELECT * FROM alerts
                WHERE audience IN ('security', 'all') OR event IN (
                    'door_open','light_intrusion','flame_ir','motion_detected'
                )
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        elif audience == "operations":
            rows = conn.execute(
                """
                SELECT * FROM alerts
                WHERE audience IN ('operations', 'all') OR event IN (
                    'overheat','overheat_warn','maintenance'
                )
                ORDER BY id DESC LIMIT ?
                """,
                (limit,),
            ).fetchall()
        else:
            rows = conn.execute(
                "SELECT * FROM alerts ORDER BY id DESC LIMIT ?", (limit,)
            ).fetchall()
    return [dict(r) for r in rows]


def list_sites() -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute("SELECT * FROM sites ORDER BY name").fetchall()
    return [dict(r) for r in rows]


def list_notifications(audience: str, limit: int = 20) -> List[Dict[str, Any]]:
    with get_connection() as conn:
        rows = conn.execute(
            "SELECT * FROM notifications WHERE audience = ? ORDER BY id DESC LIMIT ?",
            (audience, limit),
        ).fetchall()
    return [dict(r) for r in rows]


def get_site(site_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute("SELECT * FROM sites WHERE id = ?", (site_id,)).fetchone()
    return dict(row) if row else None


def get_latest_telemetry(asset_id: str) -> Optional[Dict[str, Any]]:
    with get_connection() as conn:
        row = conn.execute(
            "SELECT * FROM telemetry WHERE asset_id = ? ORDER BY id DESC LIMIT 1",
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


# Legacy compat
def list_assets() -> List[Dict[str, Any]]:
    sites = list_sites()
    return [
        {
            "id": s.get("sensor_node_id") or s["id"],
            "name": s["name"],
            "lat": s["lat"],
            "lon": s["lon"],
            "asset_type": s["facility_type"],
            "status": s["status"],
            "site_id": s["id"],
            "has_sensors": bool(s["has_sensors"]),
        }
        for s in sites if s["has_sensors"]
    ]
