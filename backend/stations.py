"""Load Gauteng power infrastructure from power-stations.json."""

from __future__ import annotations

import json
import re
from pathlib import Path
from typing import Any, Dict, List

STATIONS_FILE = Path(__file__).resolve().parent.parent / "power-stations.json"

STATUS_NORMAL = "NORMAL"
STATUS_SUSPICIOUS = "SUSPICIOUS"
STATUS_ALERT = "ALERT"
STATUS_HIGH_RISK = "HIGH RISK"
STATUS_MAINTENANCE = "MAINTENANCE"
STATUS_CRITICAL = "CRITICAL"


def _slug(name: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", name.lower()).strip("-")
    return slug[:48]


def _facility_id(name: str, prefix: str) -> str:
    return f"{prefix}-{_slug(name)}"


def load_stations_raw() -> Dict[str, Any]:
    with STATIONS_FILE.open(encoding="utf-8") as fh:
        return json.load(fh)


def flatten_stations() -> List[Dict[str, Any]]:
    """Normalize all facilities into a single list with map metadata."""
    data = load_stations_raw()
    data = data.get("gauteng_power_grid", data)
    facilities: List[Dict[str, Any]] = []

    for ps in data.get("power_stations", []):
        facilities.append({
            "id": _facility_id(ps["name"], "power-station"),
            "name": ps["name"],
            "category": "power_station",
            "facility_type": ps.get("type", "Power Station"),
            "owner": ps.get("owner", "Unknown"),
            "lat": ps["coordinates"]["latitude"],
            "lon": ps["coordinates"]["longitude"],
            "status": STATUS_NORMAL,
            "risk_score": 0,
            "has_sensors": False,
        })

    subs = data.get("substations", {})
    for group, items in subs.items():
        group_prefix = _slug(group)
        for sub in items:
            facilities.append({
                "id": _facility_id(sub["name"], group_prefix),
                "name": sub["name"],
                "category": "substation",
                "facility_type": sub.get("type", "Substation"),
                "owner": sub.get("municipality", group.replace("_", " ").title()),
                "lat": sub["coordinates"]["latitude"],
                "lon": sub["coordinates"]["longitude"],
                "status": STATUS_NORMAL,
                "risk_score": 0,
                "has_sensors": False,
            })

    # Live monitored node — John Ware is closest to hackathon demo coordinates
    for f in facilities:
        if f["name"].lower() == "john ware substation":
            f["has_sensors"] = True
            f["sensor_node_id"] = "TRANSFORMER-001"

    return facilities
